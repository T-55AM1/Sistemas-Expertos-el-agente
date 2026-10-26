import re

class TokenizerSistemasExpertos:
    def __init__(self):
        # Almacena los átomos únicos {texto_limpio: letra}
        self.tabla_atomos = {}
        # Letras disponibles para asignar
        self.letras_disponibles = ['p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
        
        # Conectores estándar para el reemplazo de texto
        self.conectores = {
            'si y solo si': ' ↔ ',
            'entonces': ' → ',
            'y': ' ∧ ',
            'o': ' ∨ ',
        }

    def limpiar_texto(self, texto):
        """Limpia puntuación, excesos de espacios y estandariza a minúsculas."""
        texto = texto.lower().strip()
        texto = re.sub(r'[.,;:]', '', texto) # Quita puntos, comas, etc.
        texto = re.sub(r'\s+', ' ', texto)   # Colapsa múltiples espacios en uno solo
        return texto

    def extraer_y_registrar_atomos(self, lineas_reglas):
        """Analiza cualquier texto ingresado para descubrir los átomos de forma dinámica."""
        frases_a_procesar = []

        for linea in lineas_reglas:
            texto_limpio = self.limpiar_texto(linea)
            if not texto_limpio:
                continue
            
            # Reemplazar temporalmente todos los conectores lógicos por un delimitador único '|'
            texto_segmentado = texto_limpio
            # Primero el más largo para evitar conflictos
            texto_segmentado = re.sub(r'\bsi\s+y\s+solo\s+si\b', ' | ', texto_segmentado)
            texto_segmentado = re.sub(r'\bsi\b', ' | ', texto_segmentated = texto_segmentado) # quita el si condicional
            texto_segmentado = re.sub(r'\bentonces\b', ' | ', texto_segmentado)
            texto_segmentado = re.sub(r'\by\b', ' | ', texto_segmentado)
            texto_segmentado = re.sub(r'\bo\b', ' | ', texto_segmentado)
            
            # Dividir por el delimitador y limpiar cada fragmento de texto
            fragmentos = [f.strip() for f in texto_segmentado.split('|') if f.strip()]
            frases_a_procesar.extend(fragmentos)

        # Registrar los átomos ignorando el "no" de la negación
        for frase in frases_a_procesar:
            # Detectar si la frase empieza con una negación libre
            if frase.startswith("no "):
                frase_atomica = frase[3:].strip()
            else:
                frase_atomica = frase

            # Si el átomo no existe en nuestro universo actual, se registra con una letra nueva
            if frase_atomica not in self.tabla_atomos and self.letras_disponibles:
                nueva_letra = self.letras_disponibles.pop(0)
                self.tabla_atomos[frase_atomica] = nueva_letra

    def traducir_a_formula(self, linea_texto):
        """Traduce cualquier oración libre a su equivalente en fórmula lógica."""
        texto_limpio = self.limpiar_texto(linea_texto)
        es_condicional = texto_limpio.startswith("si ")

        # Ordenar átomos de mayor a menor longitud para que frases largas no se rompan por palabras cortas
        atomos_ordenados = sorted(self.tabla_atomos.items(), key=lambda x: len(x[0]), reverse=True)

        # 1. Reemplazar texto por variables lógicas (mapeando negaciones automáticamente)
        for frase_atomica, letra in atomos_ordenados:
            # Reemplaza "no [frase]" por "¬letra"
            texto_limpio = re.sub(r'\bno\s+' + re.escape(frase_atomica) + r'\b', f"¬{letra}", texto_limpio)
            # Reemplaza "[frase]" por "letra"
            texto_limpio = re.sub(r'\b' + re.escape(frase_atomica) + r'\b', letra, texto_limpio)

        # 2. Traducir conectores gramaticales residuales a símbolos
        formula = texto_limpio
        
        if es_condicional:
            # Remover el "si" inicial que quedó libre
            formula = re.sub(r'^si\s+', '', formula)
            for texto_conector, simbolo in self.conectores.items():
                formula = re.sub(r'\b' + texto_conector + r'\b', simbolo, formula)
            # Agregar paréntesis requeridos por la rúbrica para fórmulas bien formadas
            formula = f"({formula})"
        else:
            for texto_conector, simbolo in self.conectores.items():
                formula = re.sub(r'\b' + texto_conector + r'\b', simbolo, formula)
        
        # Limpieza final de espacios internos de la fórmula matemática
        formula = formula.replace(" ", "")
        return formula


# --- EJECUCIÓN DINÁMICA ---
if __name__ == "__main__":
    tokenizer = TokenizerSistemasExpertos()
    
    print("=========================================================")
    print("  TOKENIZADOR DINÁMICO PARA SISTEMAS EXPERTOS")
    print("=========================================================")
    print("Instrucciones:")
    print("- Escribe tus reglas o hechos una por una.")
    print("- Puedes escribir CUALQUIER oración en español utilizando: 'y', 'o', 'no', 'si... entonces', 'si y solo si'.")
    print("- Cuando termines de ingresar tu Base de Conocimiento, escribe la palabra 'FIN'.")
    print("=========================================================\n")
    
    lineas_usuario = []
    contador = 1
    
    # Bucle infinito para capturar lo que el usuario quiera escribir en tiempo real
    while True:
        entrada = input(f"Línea {contador} > ")
        if entrada.strip().upper() == "FIN":
            break
        if entrada.strip():
            lineas_usuario.append(entrada)
            contador += 1

    if not lineas_usuario:
        print("\nNo ingresaste ninguna regla. Fin del programa.")
    else:
        print("\n--- PROCESANDO TU BASE DE CONOCIMIENTO ---\n")
        
        # 1. Aprender dinámicamente los átomos de las oraciones escritas por el usuario
        tokenizer.extraer_y_registrar_atomos(lineas_usuario)
        
        # 2. Mostrar la tabla de átomos resultante
        print("=== TABLA DE ÁTOMOS DETECTADOS ===")
        if not tokenizer.tabla_atomos:
            print("(No se detectaron átomos)")
        for frase, letra in tokenizer.tabla_atomos.items():
            print(f"{letra}: {frase}")
        print("=" * 34 + "\n")

        # 3. Mostrar la traducción de cada una de las reglas ingresadas
        print("=== BASE DE CONOCIMIENTO TRADUCIDA ===")
        for idx, linea in enumerate(lineas_usuario, 1):
            formula = tokenizer.traducir_a_formula(linea)
            print(f"R{idx}: {linea.strip()}  -->  {formula}")
        print("=" * 38)
