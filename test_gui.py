import tkinter as tk
from tkinter import messagebox

def mostrar_mensaje():
    messagebox.showinfo("Savage Worlds", "Conexión con NocoDB establecida con éxito.\n¡El Comodín está listo!")

# Configuración de la ventana
root = tk.Tk()
root.title("Savage Worlds - NocoDB Connector")
root.geometry("400x200")

label = tk.Label(root, text="Panel de Control de Datos", font=("Arial", 14))
label.pack(pady=20)

btn = tk.Button(root, text="Probar Conexión", command=mostrar_mensaje, bg="green", fg="white")
btn.pack(pady=10)

root.mainloop()