# 🛡️ KeePass to HashiCorp Vault Migrator

A Python-based GUI tool to migrate credentials from **KeePass (.kdbx)** databases to **HashiCorp Vault KVv2**. It preserves group hierarchy, normalizes paths, and includes a recursive cleanup utility.

## 📸 Screenshots
![Screenshot](https://github.com/user-attachments/assets/1d5e0f27-c7f5-47ce-8441-3514b457d2be)

## ✨ Features

* **Hierarchy Preservation:** Automatically maps KeePass groups to Vault paths.
* **Recursive Cleanup:** Deep-delete entire Vault branches before re-migrating.
* **Path Normalization:** Converts titles and groups to lowercase with underscores (Vault-friendly).
* **Security:** Supports Master Passwords and Key Files (`.key`).
* **Smart Filter:** Automatically skips the "Recycle Bin".
* **Real-time Logs:** Live feedback during the migration process.

## 🛠️ Requirements

You need Python 3.8+ and the following libraries:

```bash
pip install pykeepass hvac
