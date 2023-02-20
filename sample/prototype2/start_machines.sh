virsh net-start control
for machine in `virsh list --all --name`
do
	virsh start $machine
done
