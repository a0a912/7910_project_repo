# Recovery VM

A NixOS VM for testing file-recovery tools across ext4, Btrfs, exFAT, and NTFS.

## Run

```sh
nix run .
```

Exit the serial console with `Ctrl-A X`. Each boot provides fresh disks at `/dev/vdb` (test filesystem) and `/dev/vdc` (recovery output).

## Use

```sh
prep-fs ext4 delete
mkdir -p /mnt/out
mkfs.ext4 /dev/vdc
mount /dev/vdc /mnt/out

# run recovery command, i.e. `photorec /dev/vdb`

check-recovered /mnt/out
```

`prep-fs` creates test files and records their hashes in `/root/manifest.sha256` before deleting or reformatting the filesystem.
