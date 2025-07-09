#!/bin/bash
# Script to find the host IP address for VM connectivity

echo "=== Finding Host IP for VM Connection ==="
echo

echo "1. All network interfaces:"
ifconfig | grep -E "^[a-z]|inet " | grep -B1 "inet " | grep -v "127.0.0.1"

echo
echo "2. Common VM network interfaces:"
echo

# Check for VMware
if ifconfig | grep -q "vmnet"; then
    echo "VMware interfaces found:"
    ifconfig | grep -A1 "vmnet" | grep "inet " | awk '{print $2}'
fi

# Check for VirtualBox
if ifconfig | grep -q "vboxnet"; then
    echo "VirtualBox interfaces found:"
    ifconfig | grep -A1 "vboxnet" | grep "inet " | awk '{print $2}'
fi

# Check for Parallels
if ifconfig | grep -q "bridge"; then
    echo "Parallels/Bridge interfaces found:"
    ifconfig | grep -A1 "bridge" | grep "inet " | awk '{print $2}'
fi

# Check for UTM/QEMU
if ifconfig | grep -q "bridge100"; then
    echo "UTM/QEMU bridge found:"
    ifconfig bridge100 | grep "inet " | awk '{print $2}'
fi

echo
echo "3. Your main network IP (for bridged mode VMs):"
# Get primary interface (usually en0 or en1)
PRIMARY_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null)
if [ -n "$PRIMARY_IP" ]; then
    echo "Primary network: $PRIMARY_IP"
else
    echo "Could not determine primary IP"
fi

echo
echo "=== Instructions ==="
echo "From your VM, test connectivity to find the right IP:"
echo "1. If using NAT mode: Use the VM software's gateway IP (often 10.0.2.2 or 192.168.x.1)"
echo "2. If using Bridged mode: Use your primary network IP ($PRIMARY_IP)"
echo "3. If using Host-only mode: Use the vmnet/vboxnet IP shown above"
echo
echo "Test from VM with: nc -zv <IP> 9876"