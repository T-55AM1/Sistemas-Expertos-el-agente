if __name__ == "__main__":
    print("=== Tokenizador SAT Ultra-Robusto ===")
    print("Prueba cualquier entrada (o escribe 'salir' para finalizar)\n")
    
    # Bucle infinito para que no se cierre el programa
    while True:
        entrada = input("\nIngresa tu texto: ")
        
        # Opción para cerrar el programa limpiamente
        if entrada.lower().strip() == 'salir':
            print("¡Hasta luego!")
            break
            
        try:
            tokens, diccionario = tokenizar_robusto(entrada)
            
            if not tokens:
                print(" No se pudo extraer ninguna estructura lógica del texto ingresado.")
            else:
                print("\n[Proposiciones Extraídas]:")
                for texto, letra in diccionario.items():
                    print(f"  {letra} = \"{texto}\"")
                    
                print("\n[Fórmula SAT Resultante]:")
                # Esta línea limpia los formatos de tuplas a texto simple
                formula = " ".join([t[1] if isinstance(t, tuple) else str(t) for t in tokens])
                print(f"  {formula}")
                
        except Exception as e:
            print(f"\n Ocurrió un error inesperado al procesar la entrada: {e}")
