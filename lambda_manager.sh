#!/bin/bash

#============================================================================
# Lambda Labs Instance Manager
# Manage GPU instances via Lambda Labs API
#============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Load environment variables from .env if it exists
if [ -f "$(dirname "$0")/.env" ]; then
    export $(cat "$(dirname "$0")/.env" | grep -v '^#' | xargs)
fi

API_KEY="${LAMBDA_API_KEY}"
API_URL="https://cloud.lambdalabs.com/api/v1"

# Check if API key is set
if [ -z "$API_KEY" ]; then
    echo -e "${RED}ERROR: LAMBDA_API_KEY not set${NC}"
    echo ""
    echo "Please set your Lambda Labs API key:"
    echo "  export LAMBDA_API_KEY='your-key-here'"
    echo ""
    echo "Or add it to .env file:"
    echo "  echo 'LAMBDA_API_KEY=your-key-here' >> .env"
    exit 1
fi

# Helper function to make API calls
api_call() {
    local endpoint=$1
    local method=${2:-GET}
    local data=${3:-}

    if [ "$method" = "POST" ] && [ ! -z "$data" ]; then
        curl -s -u "${API_KEY}:" -X POST \
            -H "Content-Type: application/json" \
            -d "$data" \
            "${API_URL}${endpoint}"
    else
        curl -s -u "${API_KEY}:" "${API_URL}${endpoint}"
    fi
}

# Command: List instances
list_instances() {
    echo -e "${BLUE}Fetching your Lambda instances...${NC}"
    echo ""

    response=$(api_call "/instances")

    echo "$response" | jq -r '.data[] | "\(.id)\t\(.instance_type.name)\t\(.status)\t\(.ip)"' | \
    awk -F'\t' 'BEGIN {
        printf "%-25s %-20s %-15s %-20s\n", "INSTANCE ID", "TYPE", "STATUS", "IP ADDRESS"
        printf "%-25s %-20s %-15s %-20s\n", "-----------", "----", "------", "----------"
    } {
        printf "%-25s %-20s %-15s %-20s\n", $1, $2, $3, $4
    }'
}

# Command: List available instance types
list_types() {
    echo -e "${BLUE}Fetching available instance types...${NC}"
    echo ""

    response=$(api_call "/instance-types")

    echo "$response" | jq -r '.data | to_entries[] |
        select(.value.regions_with_capacity_available | length > 0) |
        "\(.key)\t\(.value.instance_type.price_cents_per_hour)\t\(.value.instance_type.description)"' | \
    awk -F'\t' 'BEGIN {
        printf "%-30s %-15s %-40s\n", "TYPE", "PRICE/HR", "DESCRIPTION"
        printf "%-30s %-15s %-40s\n", "----", "--------", "-----------"
    } {
        price = sprintf("$%.2f", $2/100)
        printf "%-30s %-15s %-40s\n", $1, price, $3
    }'
}

# Command: Launch instance
launch_instance() {
    local instance_type=$1
    local region=${2:-us-west-1}
    local name=${3:-sora-gpu-$(date +%s)}

    echo -e "${YELLOW}Launching instance...${NC}"
    echo "Type: $instance_type"
    echo "Region: $region"
    echo "Name: $name"
    echo ""

    data=$(jq -n \
        --arg type "$instance_type" \
        --arg region "$region" \
        --arg name "$name" \
        '{
            region_name: $region,
            instance_type_name: $type,
            ssh_key_names: [],
            file_system_names: [],
            quantity: 1,
            name: $name
        }')

    response=$(api_call "/instance-operations/launch" "POST" "$data")

    if echo "$response" | jq -e '.data.instance_ids' > /dev/null 2>&1; then
        instance_id=$(echo "$response" | jq -r '.data.instance_ids[0]')
        echo -e "${GREEN}✓ Instance launched successfully!${NC}"
        echo ""
        echo "Instance ID: $instance_id"
        echo ""
        echo "Wait 2-3 minutes for it to boot, then run:"
        echo -e "  ${CYAN}./lambda_manager.sh status${NC}"
    else
        echo -e "${RED}✗ Failed to launch instance${NC}"
        echo "$response" | jq '.'
        exit 1
    fi
}

# Command: Terminate instance
terminate_instance() {
    local instance_id=$1

    echo -e "${YELLOW}Terminating instance: $instance_id${NC}"
    echo ""

    read -p "Are you sure? This cannot be undone. (yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        echo "Cancelled."
        exit 0
    fi

    data=$(jq -n --arg id "$instance_id" '{instance_ids: [$id]}')

    response=$(api_call "/instance-operations/terminate" "POST" "$data")

    if echo "$response" | jq -e '.data.terminated_instances' > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Instance terminated${NC}"
    else
        echo -e "${RED}✗ Failed to terminate${NC}"
        echo "$response" | jq '.'
        exit 1
    fi
}

# Command: Get instance details
get_instance() {
    local instance_id=$1

    echo -e "${BLUE}Fetching instance details...${NC}"
    echo ""

    response=$(api_call "/instances/$instance_id")

    echo "$response" | jq -r '
        "ID: \(.data.id)",
        "Name: \(.data.name)",
        "Type: \(.data.instance_type.name)",
        "Status: \(.data.status)",
        "IP: \(.data.ip)",
        "Region: \(.data.region.name)"
    '
}

# Command: SSH into instance
ssh_instance() {
    local instance_id=$1

    response=$(api_call "/instances/$instance_id")
    ip=$(echo "$response" | jq -r '.data.ip')

    if [ "$ip" = "null" ] || [ -z "$ip" ]; then
        echo -e "${RED}ERROR: Could not get IP address${NC}"
        exit 1
    fi

    echo -e "${GREEN}Connecting to $ip...${NC}"
    ssh ubuntu@$ip
}

# Command: Setup and start GPU service
setup_gpu_service() {
    local instance_id=$1
    local api_key=${2:-sora-gpu-2025}

    response=$(api_call "/instances/$instance_id")
    ip=$(echo "$response" | jq -r '.data.ip')

    if [ "$ip" = "null" ] || [ -z "$ip" ]; then
        echo -e "${RED}ERROR: Could not get IP address${NC}"
        exit 1
    fi

    echo -e "${YELLOW}Setting up GPU service on $ip...${NC}"
    echo ""

    # Create setup script
    cat > /tmp/setup_gpu.sh <<'SETUPSCRIPT'
#!/bin/bash
set -e

cd ~
if [ ! -d "sora2" ]; then
    git clone https://github.com/Blurjp/sora2.git
fi

cd sora2
git pull

if [ ! -d "$HOME/Open-Sora" ]; then
    ./lambda_setup.sh
fi

# Start GPU service in tmux
tmux kill-session -t gpu 2>/dev/null || true
tmux new-session -d -s gpu "./lambda_run_gpu_service.sh --api-key ${1}"

echo ""
echo "GPU service started in tmux session 'gpu'"
echo "To view logs: tmux attach -t gpu"
SETUPSCRIPT

    chmod +x /tmp/setup_gpu.sh

    # Copy and run setup script
    echo "Copying setup script..."
    scp -o StrictHostKeyChecking=no /tmp/setup_gpu.sh ubuntu@$ip:/tmp/

    echo "Running setup (this may take 5-10 minutes)..."
    ssh -o StrictHostKeyChecking=no ubuntu@$ip "bash /tmp/setup_gpu.sh $api_key"

    echo ""
    echo -e "${GREEN}✓ GPU service is running!${NC}"
    echo ""
    echo "Update your .env file:"
    echo -e "  ${CYAN}GPU_SERVICE_URL=http://$ip:8001${NC}"
    echo -e "  ${CYAN}GPU_API_KEY=$api_key${NC}"
    echo ""
    echo "Then start local backend:"
    echo -e "  ${CYAN}./restart.sh${NC}"
}

# Main command router
case "${1:-help}" in
    list|ls)
        list_instances
        ;;
    types)
        list_types
        ;;
    launch)
        if [ -z "$2" ]; then
            echo "Usage: $0 launch <instance-type> [region] [name]"
            echo ""
            echo "Example: $0 launch gpu_1x_a100 us-west-1 my-sora-gpu"
            echo ""
            echo "Run '$0 types' to see available instance types"
            exit 1
        fi
        launch_instance "$2" "$3" "$4"
        ;;
    terminate|stop)
        if [ -z "$2" ]; then
            echo "Usage: $0 terminate <instance-id>"
            exit 1
        fi
        terminate_instance "$2"
        ;;
    info|status)
        if [ -z "$2" ]; then
            list_instances
        else
            get_instance "$2"
        fi
        ;;
    ssh)
        if [ -z "$2" ]; then
            echo "Usage: $0 ssh <instance-id>"
            exit 1
        fi
        ssh_instance "$2"
        ;;
    setup)
        if [ -z "$2" ]; then
            echo "Usage: $0 setup <instance-id> [api-key]"
            exit 1
        fi
        setup_gpu_service "$2" "$3"
        ;;
    help|*)
        echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BLUE}║         Lambda Labs Instance Manager                       ║${NC}"
        echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  list, ls              List all your instances"
        echo "  types                 List available instance types"
        echo "  launch <type>         Launch a new instance"
        echo "  terminate <id>        Terminate an instance"
        echo "  info <id>             Get instance details"
        echo "  ssh <id>              SSH into instance"
        echo "  setup <id> [key]      Setup and start GPU service"
        echo ""
        echo "Examples:"
        echo "  # List available GPU types"
        echo "  $0 types"
        echo ""
        echo "  # Launch an A100 instance"
        echo "  $0 launch gpu_1x_a100"
        echo ""
        echo "  # Check your instances"
        echo "  $0 list"
        echo ""
        echo "  # Setup GPU service on instance"
        echo "  $0 setup <instance-id> sora-gpu-2025"
        echo ""
        echo "  # SSH into instance"
        echo "  $0 ssh <instance-id>"
        echo ""
        echo "  # Terminate instance"
        echo "  $0 terminate <instance-id>"
        ;;
esac
