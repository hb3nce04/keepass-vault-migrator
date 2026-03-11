import tkinter as tk
from tkinter import filedialog, messagebox
from pykeepass import PyKeePass
import hvac

def get_vault_client(addr, token):
    if not addr or not token:
        messagebox.showwarning("Warning", "Vault address and token are required!")
        return None
    try:
        client = hvac.Client(url=addr, token=token)
        if not client.is_authenticated():
            messagebox.showerror("Error", "Vault authentication failed!")
            return None
        return client
    except Exception as e:
        messagebox.showerror("Error", f"Connection error: {str(e)}")
        return None

def browse_db():
    file = filedialog.askopenfilename(filetypes=[("KeePass DB", "*.kdbx")])
    db_entry.delete(0, tk.END)
    db_entry.insert(0, file)

def browse_key():
    file = filedialog.askopenfilename(filetypes=[("Key File", "*.key*")])
    key_entry.delete(0, tk.END)
    key_entry.insert(0, file)

def normalize(v):
    if not v:
        return "entry"
    return v.strip().lower().replace(" ", "_")

def build_group_path(entry):
    groups = []
    g = entry.group

    while g and g.name != "Root" and g.parentgroup and g.parentgroup.name != "Root":
        groups.append(normalize(g.name))
        g = g.parentgroup

    groups.reverse()
    return "/".join(groups)

def delete_recursive(client, mount_point, path):
    try:
        list_response = client.secrets.kv.v2.list_secrets(
            mount_point=mount_point,
            path=path
        )
        
        keys = list_response.get('data', {}).get('keys', [])
        
        for key in keys:
            new_path = f"{path}/{key}".strip('/')
            if key.endswith('/'):
                delete_recursive(client, mount_point, new_path)
            else:
                client.secrets.kv.v2.delete_metadata_and_all_versions(
                    mount_point=mount_point,
                    path=new_path
                )
                log_box.insert(tk.END, f"Deleted: {new_path}\n")
                log_box.see(tk.END)
                root.update_idletasks()
    except hvac.exceptions.InvalidPath:
        try:
            client.secrets.kv.v2.delete_metadata_and_all_versions(
                mount_point=mount_point,
                path=path
            )
        except:
            pass

def delete_secret_path():
    VAULT_MOUNT = "secret"
    BASE_PATH = vault_root_entry.get().strip().strip('/')

    if not BASE_PATH:
        messagebox.showwarning("Warning", "Please enter a path!")
        return

    confirm = messagebox.askyesno(
        "Warning", 
        f"Warning!\n\nThis action will RECURSIVELY delete everything under the path '{VAULT_MOUNT}/{BASE_PATH}'.\n\nAre you sure you want to proceed?"
    )
    
    if not confirm:
        return

    try:
        client = get_vault_client(vault_addr_entry.get().strip(), vault_token_entry.get().strip())
        if not client: return
        
        delete_recursive(client, VAULT_MOUNT, BASE_PATH)
        
        try:
            client.secrets.kv.v2.delete_metadata_and_all_versions(
                mount_point=VAULT_MOUNT,
                path=BASE_PATH
            )
        except:
            pass

        messagebox.showinfo("Success", f"The entire content of the '{BASE_PATH}' branch has been deleted.")

    except Exception as e:
        messagebox.showerror("Error", f"Error during recursive deletion: {str(e)}")

def run_migration():
    VAULT_MOUNT = "secret"
    base_path = vault_root_entry.get().strip().strip('/')

    try:
        db = db_entry.get()
        key = key_entry.get()
        password = pass_entry.get()

        kp = PyKeePass(db, password=password, keyfile=key if key else None)

        client = get_vault_client(vault_addr_entry.get().strip(), vault_token_entry.get().strip())
        if not client: return

        imported = 0

        for entry in kp.entries:
            group_path = build_group_path(entry).strip('/')

            if entry.group.name == "Recycle Bin" or "recycle_bin" in build_group_path(entry):
                continue

            title = normalize(entry.title)

            path_parts = []
            if base_path:
                path_parts.append(base_path)
            if group_path:
                path_parts.append(group_path)
            path_parts.append(title)
            
            final_path = "/".join(path_parts)

            secret_data = {
                "title": str(entry.title or ""),
                "username": str(entry.username or ""),
                "password": str(entry.password or ""),
                "url": str(entry.url or ""),
                "notes": str(entry.notes or "")
            }

            client.secrets.kv.v2.create_or_update_secret(
                mount_point=VAULT_MOUNT,
                path=final_path,
                secret=secret_data
            )

            log_box.insert(tk.END, f"OK: {VAULT_MOUNT.strip('/')}/{final_path.strip('/')}\n")
            log_box.see(tk.END)
            root.update_idletasks()

            imported += 1

        messagebox.showinfo("Success", f"{imported} entries successfully imported to the Vault.")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {type(e).__name__}\nMessage: {str(e)}")

root = tk.Tk()
root.title("KeePass - Vault Migrator")
root.geometry("650x500")

main_frame = tk.Frame(root, padx=15, pady=15)
main_frame.pack(fill="both", expand=True)

tk.Label(main_frame, text="Database (.kdbx)").pack()
frame_db = tk.Frame(main_frame)
frame_db.pack(fill="x")
db_entry = tk.Entry(frame_db)
db_entry.pack(side="left", fill="x", expand=True)
tk.Button(frame_db, text="Open", command=browse_db).pack(side="right")

tk.Label(main_frame, text="Key file (.key)").pack()
frame_key = tk.Frame(main_frame)
frame_key.pack(fill="x")
key_entry = tk.Entry(frame_key)
key_entry.pack(side="left", fill="x", expand=True)
tk.Button(frame_key, text="Open", command=browse_key).pack(side="right")

tk.Label(main_frame, text="Master password").pack()
pass_entry = tk.Entry(main_frame, show="*")
pass_entry.pack(fill="x")

vault_frame = tk.LabelFrame(main_frame, text="Vault configuration", padx=10, pady=10)
vault_frame.pack(fill="x", padx=10, pady=5)

tk.Label(vault_frame, text="Address").grid(row=0, column=0, sticky="w")
vault_addr_entry = tk.Entry(vault_frame)
vault_addr_entry.insert(0, "http://127.0.0.1:8200")
vault_addr_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

tk.Label(vault_frame, text="Token").grid(row=1, column=0, sticky="w")
vault_token_entry = tk.Entry(vault_frame, show="*")
vault_token_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

tk.Label(vault_frame, text="Path").grid(row=2, column=0, sticky="w")
vault_root_entry = tk.Entry(vault_frame)
vault_root_entry.insert(0, "")
vault_root_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=2)

vault_frame.columnconfigure(1, weight=1)

tk.Button(main_frame, text="Start", command=run_migration, height=2).pack(pady=10)
tk.Button(vault_frame, text="Delete Path", command=delete_secret_path, fg="red").grid(row=4, column=0, columnspan=2, pady=10)

tk.Label(main_frame, text="Log").pack()

log_box = tk.Text(main_frame, height=12)
log_box.pack(fill="both", expand=True)

root.mainloop()
