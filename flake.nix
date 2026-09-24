{
  description = "NixOS VM for testing file-recovery tools across filesystems";

  inputs.nixpkgs.url = "https://channels.nixos.org/nixos-unstable/nixexprs.tar.zst";

  outputs =
    { self, nixpkgs }:
    let
      system = "x86_64-linux";
      vm = self.nixosConfigurations.recovery-vm.config.system.build.vm;
    in
    {
      nixosConfigurations.recovery-vm = nixpkgs.lib.nixosSystem {
        inherit system;
        modules = [
          (
            { pkgs, ... }:
            let
              # Format /dev/vdb, fill it with known files, record a manifest,
              # then either delete everything or quick-reformat.
              prep-fs = pkgs.writeShellApplication {
                name = "prep-fs";
                runtimeInputs = with pkgs; [
                  coreutils
                  gawk
                  util-linux
                  imagemagick

                  e2fsprogs
                  btrfs-progs
                  exfatprogs
                  ntfs3g
                ];
                text = ''
                  fs=''${1:?usage: prep-fs <ext4|btrfs|exfat|ntfs> [delete|reformat] [device]}
                  mode=''${2:-delete}
                  dev=''${3:-/dev/vdb}
                  mnt=/mnt/test

                  mkfs_dev() {
                    case $fs in
                      ext4) "mkfs.$fs" -q -F "$dev" ;;
                      btrfs) mkfs.btrfs -q -f "$dev" ;;
                      exfat) mkfs.exfat "$dev" ;;
                      ntfs)  mkfs.ntfs -F -Q "$dev" ;;
                      *) echo "unsupported fs: $fs" >&2; exit 1 ;;
                    esac
                  }

                  mount_dev() {
                    if [ "$fs" = ntfs ]; then
                      mount -t ntfs-3g "$dev" "$mnt"
                    else
                      mount "$dev" "$mnt"
                    fi
                  }

                  mountpoint -q "$mnt" && umount "$mnt"
                  mkdir -p "$mnt"

                  echo ">> mkfs.$fs on $dev"
                  mkfs_dev
                  mount_dev

                  echo ">> populating"
                  mkdir -p "$mnt"/{docs,photos,bin}
                  awk -v dir="$mnt/docs" '
                    BEGIN {
                      for (i = 1; i <= 20; i++) {
                        file = sprintf("%s/doc%d.txt", dir, i)
                        for (j = 1; j <= i * 500; j++)
                          print "file " i " line " j > file
                        close(file)
                      }
                    }
                  '
                  args=()
                  for i in {1..10}; do
                    args+=( -size 1024x768 plasma:fractal )
                  done
                  magick "''${args[@]}" +adjoin "$mnt/photos/img%d.jpg"
                  for i in 1 2 3; do
                    head -c $(( i * 3 ))M /dev/urandom > "$mnt/bin/blob$i.bin"
                  done
                  sync -f "$mnt"

                  echo ">> writing manifest to /root/manifest.sha256"
                  (cd "$mnt" && find . -type f -exec sha256sum {} +) | sort -k2 > /root/manifest.sha256

                  case $mode in
                    delete)
                      echo ">> deleting everything"
                      rm -rf "''${mnt:?}"/*
                      sync -f "$mnt"
                      umount "$mnt"
                      ;;
                    reformat)
                      echo ">> quick reformat (same fs)"
                      umount "$mnt"
                      mkfs_dev
                      ;;
                    *) echo "unknown mode: $mode" >&2; exit 1 ;;
                  esac

                  echo ">> done: $dev is unmounted and ready for recovery attempts"
                '';
              };

              # Compare recovered files against the manifest by content hash
              # (names are usually lost, so match on sha256 only).
              check-recovered = pkgs.writeShellApplication {
                name = "check-recovered";
                runtimeInputs = with pkgs; [
                  coreutils
                  findutils
                  gawk
                ];
                text = ''
                  dir=''${1:?usage: check-recovered <dir-with-recovered-files>}
                  found=$(mktemp)
                  trap 'rm -f "$found"' EXIT
                  find "$dir" -type f -exec sha256sum {} + | awk '{print $1}' | sort -u > "$found"

                  awk '
                    BEGIN { hit = 0; total = 0 }
                    FILENAME == ARGV[1] { found[$1] = 1; next }
                    {
                      file = $0
                      sub(/^[^[:space:]]+[[:space:]]+/, "", file)
                      total++
                      if ($1 in found) {
                        hit++
                      } else {
                        print "MISS " file
                      }
                    }
                    END {
                      printf "%d/%d files recovered byte-for-byte\n", hit, total
                    }
                  ' "$found" /root/manifest.sha256
                '';
              };
            in
            {
              networking.hostName = "recovery-vm";
              system.stateVersion = "26.05";

              boot.supportedFilesystems = [
                "ext4"
                "btrfs"
                "exfat"
                "ntfs"
              ];

              services.getty.autologinUser = "root";

              virtualisation.vmVariant.virtualisation = {
                graphics = false; # serial console in your terminal (Ctrl-A X to quit)
                cores = 4;
                memorySize = 4096;
                # Fresh blank disks on every boot:
                #   /dev/vdb = filesystem under test
                #   /dev/vdc = output target for recovered files
                # (/dev/vda is the VM's own root disk)
                emptyDiskImages = [
                  2048
                  2048
                ];
              };

              environment.systemPackages = [
                prep-fs
                check-recovered
              ]
              ++ (with pkgs; [
                # recovery / carving
                testdisk # provides photorec
                ddrescue

                # fs tooling
                e2fsprogs
                btrfs-progs
                exfatprogs
                ntfs3g

                # misc
                util-linux
                parted
                gptfdisk
                file
                tree
                hexdump
              ]);
            }
          )
        ];
      };

      packages.${system}.default = vm;

      apps.${system}.default = {
        type = "app";
        program = "${vm}/bin/run-recovery-vm-vm";
      };
    };
}
