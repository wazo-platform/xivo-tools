1) Général
1.1) Construction de xbr (XiVO Backup And Restore)
xbr est basé sur un live Debian Squeeze.
Un script permet de générer le live "live_build.sh", en prérecquis il faut :
	-Debian Squeeze
	-Paquet live-build
	-Proxy apt-cacher
Ensuite en root exécuter le script "live_build.sh".
Dans le dossier "/live" vous trouverez le live contruit.

1.2) Architecture du disque
Deux partition sont construites :
	1 => Partition SYSTEM bootable contenant xbr (Live Debian Squeeze + Scripts).
	2 => Partion DATA contenant l'intégralité des sauvegardes dans le dossier "backup" disponibles sur le média de stockage.

1.3) Architecture soft
Boot de Debian Squeze se charge...
Auto login, ensuite le script "/live/image/xbr/menu" est exécuté.
Un menu à choix s'affiche.

				NOOB
1) Backup
-Démarrer sur la clé
-Faire [1] est [ENTRER]
-Mettre le nom de la sauvegarde (Nom différent d'une autre sauvegarde)
-Renseigné le disque à sauvegarder (Exemple : sda, sdb, ...)
-PATIENTER
-Reboot

2) Restore
-Démarrer sur la clé
-Faire [2] est [ENTRER]
-Mettre le nom de la sauvegarde à restaurer (Elle sont listé)
-Renseigné le disque à restaurer
-PATIENTER
-Reboot

3) Install to other disk
-Démarrer sur la clé
-Faire [3] est [ENTRER]
-Renseigné le disque sur le quel xbr sera installer (ATTENTION LE MEDIA SERA TOTALEMENT EFFACE)
-PATIENTER
-Reboot
