import re

class TokenizadorSistemasExpertos:
    def __init__(self):
        # Tabla global de átomos {texto_limpio: letra}
        self.tabla_atomos = {}
        self.letras_disponibles = ['p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
        
        # Palabras clave y sinónimos del español mapeados a tokens lógicos
        self.palabras_clave = {
            'y': 'CONJ',
            'pero': 'CONJ',
            'o': 'DISJ',
            'no': 'NEG',
            'si': 'COND_SI',
            'entonces': 'COND_ENTONCES',
            'si y solo si': 'BICOND'
        }

    def limpiar_texto(self, texto):
        """Limpia puntuación destructiva, dejando las comas si actúan como pausas."""
        texto = texto.lower().strip()
        texto = re.sub(r'[.;:]', '', texto)  # Quita puntos y dos puntos
        texto = re.sub(r'\s+', ' ', texto)   # Estandariza espacios
        return texto

    def segmentar_palabras(self, texto):
        """Convierte una cadena de texto en una lista de palabras/conectores limpios."""
        texto = self.limpiar_texto(texto)
        # Proteger conectores compuestos
        texto = re.sub(r'\bsi\s+y\s+solo\s+si\b', '##BICOND##', texto)
        
        # Tratar comas solas seguidas de conectores o que actúan como "y"
        texto = re.sub(r',\s+pero\b', ' pero', texto)
        texto = re.sub(r',\s+y\b', ' y', texto)
        
        tokens_preliminares = texto.split()
        tokens_finales = []
        
        for t in tokens_preliminares:
            # Limpiar comas residuales de las palabras
            t_limpio = t.replace(',', '')
            if t == '##BICOND##':
                tokens_finales.append('si y solo si')
            elif t_limpio in self.palabras_clave:
                tokens_finales.append(t_limpio)
            elif t_limpio:
                tokens_finales.append(t_limpio)
        return tokens_finales

    def registrar_atomos_de_base(self, lineas):
        """Fase 1: Extrae y registra todos los átomos de la base de conocimientos."""
        for linea in lineas:
            palabras = self.segmentar_palabras(linea)
            if not palabras:
                continue
            
            buffer_atomo = []
            for palabra in palabras:
                if palabra in self.palabras_clave:
                    if buffer_atomo:
                        self._guardar_atomo_puro(buffer_atomo)
                        buffer_atomo = []
                else:
                    buffer_atomo.append(palabra)
            
            if buffer_atomo:
                self._guardar_atomo_puro(buffer_atomo)

    def _guardar_atomo_puro(self, lista_palabras):
        """Remueve negaciones iniciales antes de indexar en la tabla."""
        if lista_palabras and lista_palabras[0] == 'no' and len(lista_palabras) > 1:
            texto_atomo = " ".join(lista_palabras[1:])
        else:
            texto_atomo = " ".join(lista_palabras)
            
        if texto_atomo and texto_atomo not in self.tabla_atomos and self.letras_disponibles:
            self.tabla_atomos[texto_atomo] = self.letras_disponibles.pop(0)

    def buscar_letra_atomo(self, lista_palabras):
        """Encuentra la letra de un átomo o devuelve vacío si no contiene palabras válidas."""
        if not lista_palabras:
            return ""
        
        if lista_palabras[0] == 'no' and len(lista_palabras) > 1:
            texto = " ".join(lista_palabras[1:])
            es_negado = True
        else:
            texto = " ".join(lista_palabras)
            es_negado = False
            
        letra = self.tabla_atomos.get(texto, "")
        if not letra:
            return ""
        return f"¬{letra}" if es_negado else letra

    def traducir_oracion(self, linea_texto):
        """Fase 2: Traduce cualquier flujo de texto largo evaluando tokens secuencialmente."""
        palabras = self.segmentar_palabras(linea_texto)
        if not palabras:
            return ""

        # Manejo especial si la oración empieza directamente con "si "
        es_condicional_estandar = (palabras[0] == 'si') if palabras else False

        componentes_formula = []
        buffer_atomo = []
        
        i = 0
        while i < len(palabras):
            palabra = palabras[i]
            
            if palabra in self.palabras_clave:
                # Al encontrar un conector, procesamos el átomo acumulado
                if buffer_atomo:
                    letra = self.buscar_letra_atomo(buffer_atomo)
                    if letra: componentes_formula.append(letra)
                    buffer_atomo = []
                
                tipo_conector = self.palabras_clave[palabra]
                
                if tipo_conector == 'CONJ':
                    componentes_formula.append('∧')
                elif tipo_conector == 'DISJ':
                    componentes_formula.append('∨')
                elif tipo_conector == 'BICOND':
                    componentes_formula.append('↔')
                elif tipo_conector == 'COND_ENTONCES':
                    componentes_formula.append('→')
                elif tipo_conector == 'COND_SI':
                    # Si el 'si' está en medio de la oración (ej: "p si q")
                    if i > 0:
                        componentes_formula.append('←') # Marcador temporal de inversión
            else:
                buffer_atomo.append(palabra)
            i += 1

        if buffer_atomo:
            letra = self.buscar_letra_atomo(buffer_atomo)
            if letra: componentes_formula.append(letra)

        # Re-estructurar en caso de haber encontrado un condicional invertido '←'
        if '←' in componentes_formula:
            idx_flecha = componentes_formula.index('←')
            consecuencia = componentes_formula[:idx_flecha]
            condicion = componentes_formula[idx_flecha+1:]
            
            # Reordenar matemáticamente: (condicion → consecuencia)
            str_condicion = "".join(condicion)
            str_consecuencia = "".join(consecuencia)
            formula_final = f"({str_condicion}→{str_consecuencia})"
        else:
            formula_final = "".join(componentes_formula)
            if es_condicional_estandar and '→' in formula_final:
                # Quitar el token del 'si' inicial si quedó pegado y añadir paréntesis formales
                formula_final = formula_final.replace('si', '')
                formula_final = f"({formula_final})"

        return formula_final

    def procesar(self, lineas_usuario):
        self.registrar_atomos_de_base(lineas_usuario)
        
        print("\n=== TABLA DE ÁTOMOS DETECTADOS ===")
        for frase, letra in self.tabla_atomos.items():
            print(f"{letra} = \"{frase}\"")
        print("==================================\n")

        print("=== BASE DE CONOCIMIENTO TRADUCIDA ===")
        for idx, linea in enumerate(lineas_usuario, 1):
            formula = self.traducir_oracion(linea)
            print(f"R{idx}: {linea.strip()}  -->  {formula}")
        print("======================================")

# --- EJECUCIÓN INTERACTIVA ---
if __name__ == "__main__":
    tokenizador = TokenizadorSistemasExpertos()
    
    print("=============================================================")
    print("  TOKENIZADOR EXPERTO SAT V4.0 (PROCESAMIENTO DE TEXTO LARGO)")
    print("=========================================================")
    print("Escribe tus reglas complejas. Al terminar, escribe 'FIN'.    ")
    print("===========================================================\n")
    
    lineas_usuario = []
    contador = 1
    
    while True:
        entrada = input(f"Línea {contador} > ")
        if entrada.strip().upper() == "FIN":
            break
        if entrada.strip():
            lineas_usuario.append(entrada)
            contador += 1

    if lineas_usuario:
        tokenizador.procesar(lineas_usuario)
