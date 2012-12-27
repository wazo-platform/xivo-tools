#!/bin/bash
# Dossier racine
racine="/live"
# URL (Dossier) des packages
config_url="127.0.0.1/xbr"
# Proxy apt-get
proxy_apt="127.0.0.1:3142"

# Un petit coup de menage
cd "/"
rm -r "$racine"; mkdir -p "$racine"
cd "$racine"; lb clean

# LiveBuild config
lb config \
   --architecture "i386" \
   --binary-images "iso" \
   --distribution "squeeze" \
   --packages-lists "minimal" \
   --mirror-bootstrap "http://$proxy_apt/ftp.fr.debian.org/debian/" \
   --mirror-chroot "http://ftp.fr.debian.org/debian/" \
   --archive-areas "main contrib non-free" \
   --bootappend-live "locales=fr_FR.UTF-8 keyboard-layouts=fr" \
   --packages "screen hfsutils hfsprogs jfsutils ntfsprogs reiser4progs xfsprogs btrfs-tools lvm2 parted grub2 iotop smartmontools bash-completion htop console-data vim nano" \
   --language "fr" \
   --hostname "debianlive" \
   --username "live" \
   --memtest "none" \
   --syslinux-timeout "5" \
   --interactive "false" \
   --win32-loader "false" \
   --clean \

# Creation des repertoires par defaut
mkdir -p "$racine/chroot/etc/apt" "$racine/config/chroot_local-hooks" "$racine/config/chroot_local-includes"

# Applications des configurations
### Script POST-INSTALL ###
echo '#!/bin/sh' > "$racine/config/chroot_local-hooks/post_install.sh"
echo 'echo "/live/image/xbr/menu" >> "/etc/skel/.bashrc"' >> "$racine/config/chroot_local-hooks/post_install.sh"
echo "sed -i -e 's!2:23:respawn:/sbin/getty 38400 tty2!#2:23:respawn:/sbin/getty 38400 tty2!g' /etc/inittab" >> "$racine/config/chroot_local-hooks/post_install.sh"
echo "sed -i -e 's!3:23:respawn:/sbin/getty 38400 tty3!#3:23:respawn:/sbin/getty 38400 tty3!g' /etc/inittab" >> "$racine/config/chroot_local-hooks/post_install.sh"
echo "sed -i -e 's!4:23:respawn:/sbin/getty 38400 tty4!#4:23:respawn:/sbin/getty 38400 tty4!g' /etc/inittab" >> "$racine/config/chroot_local-hooks/post_install.sh"
echo "sed -i -e 's!5:23:respawn:/sbin/getty 38400 tty5!#5:23:respawn:/sbin/getty 38400 tty5!g' /etc/inittab" >> "$racine/config/chroot_local-hooks/post_install.sh"
echo "sed -i -e 's!6:23:respawn:/sbin/getty 38400 tty6!#6:23:respawn:/sbin/getty 38400 tty6!g' /etc/inittab" >> "$racine/config/chroot_local-hooks/post_install.sh"
chmod -R 755 "$racine/config/chroot_local-hooks"

### Proxy apt-cacher ###
echo 'Acquire::http { Proxy "http://'$proxy_apt'"; };' > "chroot/etc/apt/apt.conf"

### VERSION ###
echo 'debian_6_32.2.0.5' >> "$racine/config/chroot_local-includes/VERSION"

# Generation du live
lb build
