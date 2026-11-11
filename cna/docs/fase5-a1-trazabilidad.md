# Trazabilidad de los accesos de A1

Cada rango se extrajo del paquete de código de la VM. La numeración corresponde al archivo original. Los hashes permiten contrastar el archivo completo con el paquete recibido.

| Ref. | Archivo | Líneas | SHA-256 del archivo completo |
|---|---|---|---|
| R01 | `app/Entities/Models/Entity.php` | 80–134 | `41284867ba14d8bb7dddeb868685d1f96a2066f1af4b42648b8df6b75c3b3f62` |
| R01 | `app/Entities/Models/EntityPageData.php` | 1–25 | `4d689bd12480d54d22bb14270e7c7b5a719ee3d1c23e963485fbc1d55497e7e1` |
| R01 | `app/Entities/Models/EntityContainerData.php` | 1–50 | `13d8374ea806976b6d9399eac26408544660251caf5f564f3df6ff78855e2131` |
| R01 | `app/Entities/Models/EntityScope.php` | 14–28 | `f35d59fc602621425c25ba81c327b6fcbc3978856ac98e6f47a6da102b651c16` |
| R01 | `app/Entities/Models/EntityQueryBuilder.php` | 10–22 | `e9acfe9517cfb47c3946ef06be0ac21365460760e6d11acce2848a4b4dbc8631` |
| R02 | `app/Entities/Repos/BaseRepo.php` | 42–106 | `309f33814ee9e0b204c0d48d8a75ad7164e1e7970553b38a59aa6c6901834aae` |
| R02 | `app/Entities/Repos/PageRepo.php` | 119–149 | `2bbe8fbc4d766079ff0ef8a3d130dbf3494688f27cb8e5ccbb1d9eb899e711e9` |
| R03 | `app/Entities/Repos/RevisionRepo.php` | 19–90 | `d3e83c6b0635e55f389b987138f00337f91bc798c728c9e5b9963efaface387f` |
| R04 | `app/Search/SearchIndex.php` | 35–115 | `481ebb505d11bcf56dc7d1b72e9b72620456e72b779ab16a5609347c76ba960c` |
| R04 | `app/Search/SearchIndex.php` | 274–296 | `481ebb505d11bcf56dc7d1b72e9b72620456e72b779ab16a5609347c76ba960c` |
| R04 | `app/Search/SearchRunner.php` | 155–185 | `d3bc0320bba002ebcdadcc3039af0a78037f4d85b2a92d0798ea1597be8bd27f` |
| R04 | `app/Search/SearchTerm.php` | 1–21 | `2c60a20f964e82e2e7d316f4fcd94241a02629c216e667ed9b035bb185ef649e` |
| R04 | `app/Entities/Models/Entity.php` | 395–408 | `41284867ba14d8bb7dddeb868685d1f96a2066f1af4b42648b8df6b75c3b3f62` |
| R05 | `app/Activity/Tools/ActivityLogger.php` | 24–105 | `05f9d7fc82db211dba1afc5861d69162292c63bf262e046beccab04feb62e41b` |
| R05 | `app/Activity/Models/Activity.php` | 26–54 | `92b4d0a2ae07f42573c1602d34d5176523e2fab3703194e6a2218462e9876f4c` |
| R05 | `app/Activity/ActivityQueries.php` | 28–97 | `78262a245fa696701583647fc7b360ccabcba715416ca16aa808582ee7dfe104` |
| R06 | `app/Exports/Controllers/PageExportApiController.php` | 14–79 | `3e92ae2898fbc22276ab915a5416a0616c10939f38cffbc0535d2ff42565cd48` |
| R06 | `app/Exports/Controllers/BookExportApiController.php` | 14–79 | `906c26297af183f8cac583d7bc0e41bee0a149d6e54c315d6f85f7065bd74878` |
| R06 | `app/Exports/ExportFormatter.php` | 93–146 | `9ac4cbc5e89f368b583432a45b31ace9359c746fdb1b7e3f56e55cece5ff9dca` |
| R06 | `app/Exports/ExportFormatter.php` | 295–346 | `9ac4cbc5e89f368b583432a45b31ace9359c746fdb1b7e3f56e55cece5ff9dca` |
| R06 | `app/Entities/Tools/BookContents.php` | 43–105 | `f486badfb8f9a79ffcee7b1299f79e44570991efe0568b20f02814f9408a6ebc` |
| R06 | `app/Exports/ZipExports/Models/ZipExportPage.php` | 40–59 | `a5bc68e9ee306dd66200bdb1a4cfb7658d38afe785f0f5ddd04db0d57e18e2a3` |
| R06 | `app/Exports/ZipExports/ZipExportFiles.php` | 82–107 | `839898859722aa300494a8999e7a8dc258ae97a5325f9583dd2a17e40cbe085a` |
| R07 | `app/Uploads/Image.php` | 24–51 | `98dad68df23771e72fee9b72a7b07363ee27da3f7793a53571b539930944035e` |
| R07 | `app/Uploads/ImageService.php` | 71–114 | `2d5ce49d0911a05646ef20a7e48a4d03b58e8a342254f33e7e499a8480be049f` |
| R07 | `app/Uploads/ImageService.php` | 156–206 | `2d5ce49d0911a05646ef20a7e48a4d03b58e8a342254f33e7e499a8480be049f` |
| R07 | `app/Uploads/ImageRepo.php` | 20–42 | `7d11fb146b5044f1141e4b5e952d496a426af315a620eaf67a47927a7892712a` |
| R08 | `app/Uploads/Attachment.php` | 32–62 | `d0291cb5d230f4369337134b49e69acf0c2dcf65dd5811e462dc699ef7f24fc1` |
| R08 | `app/Uploads/Attachment.php` | 110–125 | `d0291cb5d230f4369337134b49e69acf0c2dcf65dd5811e462dc699ef7f24fc1` |
| R08 | `app/Uploads/AttachmentService.php` | 39–58 | `50921de300513e9ab564066096c04e51ad48dda5865d113305f095011d2c754c` |
| R08 | `app/Uploads/AttachmentService.php` | 105–159 | `50921de300513e9ab564066096c04e51ad48dda5865d113305f095011d2c754c` |
| R08 | `app/Uploads/Controllers/AttachmentApiController.php` | 27–57 | `29b3b81e5de216ca7c45340855f66dcbe79f6e00216d94fddb8f38a4e5224308` |
| R09 | `app/Users/Models/User.php` | 55–64 | `f0a8c72691901d99401fa28b653391a1fe69c7015ba86d1f496a771a69c61cb0` |
| R09 | `app/Users/Models/User.php` | 120–125 | `f0a8c72691901d99401fa28b653391a1fe69c7015ba86d1f496a771a69c61cb0` |
| R09 | `app/Users/Models/User.php` | 164–181 | `f0a8c72691901d99401fa28b653391a1fe69c7015ba86d1f496a771a69c61cb0` |
| R09 | `app/Users/Models/Role.php` | 39–102 | `ecac59383529a0b3a0265748a66ad87fb718a5f37ddbcbb896ff828bbe6f6707` |
| R09 | `app/Users/UserRepo.php` | 78–102 | `9ff3c33e0396f71cada9f2aa747df7e6a988806609290b1bafd9101cd16eef9e` |
| R09 | `app/Users/UserRepo.php` | 205–265 | `9ff3c33e0396f71cada9f2aa747df7e6a988806609290b1bafd9101cd16eef9e` |
| R09 | `app/Users/UserRepo.php` | 300–312 | `9ff3c33e0396f71cada9f2aa747df7e6a988806609290b1bafd9101cd16eef9e` |
| R09 | `app/Permissions/PermissionsRepo.php` | 26–117 | `656865cdaefff9f1834570d1654673b130eed6933d81f28bf724a0c540f439c0` |
| R10 | `app/Entities/Tools/PermissionsUpdater.php` | 22–101 | `6aef1fc704d67f21c8c2476f9006826bb2861211537383afff62b9a1791b3f3a` |
| R10 | `app/Permissions/PermissionApplicator.php` | 102–123 | `346780ae63004739a40870efec144e97781fc117722358d62f56dcf7d7291840` |
| R10 | `app/Permissions/PermissionApplicator.php` | 132–155 | `346780ae63004739a40870efec144e97781fc117722358d62f56dcf7d7291840` |
| R10 | `app/Permissions/PermissionApplicator.php` | 192–210 | `346780ae63004739a40870efec144e97781fc117722358d62f56dcf7d7291840` |
| R10 | `app/Permissions/JointPermissionBuilder.php` | 32–49 | `e83228f7a21b5bc400dd2804023fd1105706ced98e1b9a96fcf41bd39c99ddad` |
| R10 | `app/Permissions/JointPermissionBuilder.php` | 161–174 | `e83228f7a21b5bc400dd2804023fd1105706ced98e1b9a96fcf41bd39c99ddad` |
| R10 | `app/Permissions/JointPermissionBuilder.php` | 199–233 | `e83228f7a21b5bc400dd2804023fd1105706ced98e1b9a96fcf41bd39c99ddad` |
| R10 | `app/Permissions/EntityPermissionEvaluator.php` | 116–139 | `6db62519910e3c4004ad1c87aba2a64d32035c8a477d266800b3a518f98acefb` |
| R11 | `app/Entities/Repos/BookshelfRepo.php` | 61–91 | `6a55417f107e41c492e0860f5eb899c02d985493329a5b426bb17416a00f5eb0` |
| R11 | `app/Activity/TagRepo.php` | 137–156 | `6cbe05be7fcf0d4cbeca08cf576cd32d9541b99fdc88c932dd92a460dc37667e` |
