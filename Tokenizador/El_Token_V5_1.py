import re

# ==============================================================================
# 1. PARTE: TOKENIZADOR Y TRADUCTOR DE LENGUAJE NATURAL ORIGINAL
# ==============================================================================
class TokenizadorSistemasExpertos:
    def __init__(self):
        self.tabla_atomos = {}
        self.letras_disponibles = ['p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
        self.palabras_clave = {
            'y': 'CONJ', 'pero': 'CONJ', 'e': 'CONJ',
            'o': 'DISJ', 'u': 'DISJ',
            'no': 'NEG',
            'si': 'COND_SI', 'entonces': 'COND_ENTONCES',
            'si y solo si': 'BICOND'
        }

    def limpiar_texto(self, texto):
        texto = texto.lower().strip()
        if texto.startswith("si ") and " entonces " not in texto and "," in texto:
            texto = texto.replace(",", " entonces", 1)
        re_chars = re.compile(r'[.;:]')
        texto = re_chars.sub('', texto)
        texto = texto.replace(',', '')
        re_spaces = re.compile(r'\s+')
        texto = re_spaces.sub(' ', texto)
        return texto

    def segmentar_palabras(self, texto):
        texto = self.limpiar_texto(texto)
        re_bicond = re.compile(r'\bsi\s+y\s+solo\s+si\b')
        texto = re_bicond.sub('##BICOND##', texto)
        tokens_preliminares = texto.split()
        tokens_finales = []
        for t in tokens_preliminares:
            if t == '##BICOND##':
                tokens_finales.append('si y solo si')
            else:
                tokens_finales.append(t)
        return tokens_finales

    def registrar_atomos_de_base(self, lineas):
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
        if lista_palabras and lista_palabras[0] == 'no' and len(lista_palabras) > 1:
            texto_atomo = " ".join(lista_palabras[1:])
        else:
            texto_atomo = " ".join(lista_palabras)
        if texto_atomo and texto_atomo not in self.tabla_atomos and self.letras_disponibles:
            self.tabla_atomos[texto_atomo] = self.letras_disponibles.pop(0)

    def buscar_letra_atomo(self, lista_palabras):
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
        palabras = self.segmentar_palabras(linea_texto)
        if not palabras:
            return ""
        es_condicional_estandar = (palabras[0] == 'si') if palabras else False
        componentes_formula = []
        buffer_atomo = []
        i = 0
        while i < len(palabras):
            palabra = palabras[i]
            if palabra in self.palabras_clave:
                if buffer_atomo:
                    letra = self.buscar_letra_atomo(buffer_atomo)
                    if letra: componentes_formula.append(letra)
                    buffer_atomo = []
                tipo_conector = self.palabras_clave[palabra]
                if tipo_conector == 'CONJ': componentes_formula.append('∧')
                elif tipo_conector == 'DISJ': componentes_formula.append('∨')
                elif tipo_conector == 'BICOND': componentes_formula.append('↔')
                elif tipo_conector == 'COND_ENTONCES': componentes_formula.append('→')
                elif tipo_conector == 'NEG': buffer_atomo.append(palabra)
            else:
                buffer_atomo.append(palabra)
            i += 1

        if buffer_atomo:
            letra = self.buscar_letra_atomo(buffer_atomo)
            if letra: componentes_formula.append(letra)
        if componentes_formula and componentes_formula[0] == 'si':
            componentes_formula.pop(0)

        formula_final = "".join(componentes_formula)
        if es_condicional_estandar and '→' in formula_final:
            formula_final = f"({formula_final})"
        return formula_final

# ==============================================================================
# 2. PARTE: ANALIZADOR SINTÁCTICO DE FÓRMULAS LÓGICAS
# ==============================================================================
class AnalizadorFormulas:
    def quitar_parentesis_externos(self, f):
        while f.startswith('(') and f.endswith(')'):
            balance = 0
            completo = True
            for idx, c in enumerate(f[:-1]):
                if c == '(': balance += 1
                elif c == ')': balance -= 1
                if balance == 0 and idx > 0:
                    completo = False
                    break
            if completo: f = f[1:-1]
            else: break
        return f

    def encontrar_conector_principal(self, f):
        f = self.quitar_parentesis_externos(f)
        if len(f) == 1 and f.isalpha():
            return 'ATOMO', f, None
        if len(f) == 2 and f.startswith('¬') and f[1:].isalpha():
            return 'ATOMO_NEGADO', f[1:], None

        conectores = ['↔', '→', '∨', '∧']
        for conector in conectores:
            balance = 0
            for idx in range(len(f) - 1, -1, -1):
                c = f[idx]
                if c == ')': balance += 1
                elif c == '(': balance -= 1
                elif balance == 0 and c == conector:
                    izq = f[:idx]
                    der = f[idx+1:]
                    if conector == '∧': tipo = 'CONJUNCION'
                    elif conector == '∨': tipo = 'DISJUNCION'
                    elif conector == '→': tipo = 'CONDICIONAL'
                    elif conector == '↔': tipo = 'BICONDICIONAL'
                    return tipo, izq, der

        if f.startswith('¬'):
            return 'NEGACION', f[1:], None
        return 'ATOMO', f, None

# ==============================================================================
# 3. PARTE: ESTRUCTURA DEL ÁRBOL SEMÁNTICO
# ==============================================================================
class NodoArbolSemantico:
    _id_counter = 0

    def __init__(self, formulas, atomos_afirmados=None, atomos_negados=None, regla_origen=""):
        NodoArbolSemantico._id_counter += 1
        self.id = NodoArbolSemantico._id_counter
        self.formulas = list(formulas)
        self.atomos_afirmados = set(atomos_afirmados) if atomos_afirmados else set()
        self.atomos_negados = set(atomos_negados) if atomos_negados else set()
        self.regla_origen = regla_origen
        self.izquierdo = None
        self.derecho = None
        self.cerrada = False

    def verificar_contradiccion(self):
        interseccion = self.atomos_afirmados.intersection(self.atomos_negados)
        if interseccion:
            self.cerrada = True
            return True
        return False

    def obtener_etiqueta(self):
        lineas = []
        if self.formulas:
            lineas.append("Pendientes:")
            for f in self.formulas: lineas.append(f"  {f}")
        literales = []
        for a in sorted(list(self.atomos_afirmados)): literales.append(f"{a}=V")
        for n in sorted(list(self.atomos_negados)): literales.append(f"{n}=F")
        if literales:
            lineas.append("Estado Actual:")
            lineas.append(f"  [{', '.join(literales)}]")
        if self.cerrada: lineas.append("✕ CONTRADICCIÓN")
        elif not self.izquierdo and not self.derecho: lineas.append("✅ RAMA ABIERTA")
        return "\\n".join(lineas)

# ==============================================================================
# 4. PARTE: MOTOR ITERATIVO (BLINDADO - EVITA RECURSIONERROR E INFINITOS)
# ==============================================================================
class MotorInferencia:
    def __init__(self):
        self.analizador = AnalizadorFormulas()
        self.modelos_encontrados = []

    def construir_arbol(self, nodo_raiz):
        pila_trabajo = [nodo_raiz]

        while pila_trabajo:
            nodo = pila_trabajo.pop()

            if nodo.verificar_contradiccion():
                continue

            formulas_restantes = []
            for f in nodo.formulas:
                tipo, izq, der = self.analizador.encontrar_conector_principal(f)
                if tipo == 'ATOMO': nodo.atomos_afirmados.add(izq)
                elif tipo == 'ATOMO_NEGADO': nodo.atomos_negados.add(izq)
                else: formulas_restantes.append(f)

            if nodo.verificar_contradiccion():
                continue
            if not formulas_restantes:
                continue

            formula_elegida = None
            tipo_elegido = None
            sub_izq, sub_der = None, None

            for f in formulas_restantes:
                tipo, izq, der = self.analizador.encontrar_conector_principal(f)
                if tipo in ['CONJUNCION']:
                    formula_elegida = f
                    tipo_elegido = tipo
                    sub_izq, sub_der = izq, der
                    break
                elif tipo == 'NEGACION':
                    tipo_interno, int_izq, int_der = self.analizador.encontrar_conector_principal(izq)
                    if tipo_interno in ['DISJUNCION', 'CONDICIONAL']:
                        formula_elegida = f
                        tipo_elegido = f"NEG_{tipo_interno}"
                        sub_izq, sub_der = int_izq, int_der
                        break

            if not formula_elegida:
                formula_elegida = formulas_restantes[0]
                tipo_elegido, sub_izq, sub_der = self.analizador.encontrar_conector_principal(formula_elegida)
                if tipo_elegido == 'NEGACION':
                    tipo_interno, int_izq, int_der = self.analizador.encontrar_conector_principal(sub_izq)
                    if tipo_interno in ['CONJUNCION', 'BICONDICIONAL']:
                        tipo_elegido = f"NEG_{tipo_interno}"
                        sub_izq, sub_der = int_izq, int_der

            pendientes_siguientes = [f for f in formulas_restantes if f != formula_elegida]

            # REGLAS ALFA (1 Rama)
            if tipo_elegido == 'CONJUNCION':
                pendientes_siguientes.extend([sub_izq, sub_der])
                nodo.izquierdo = NodoArbolSemantico(pendientes_siguientes, nodo.atomos_afirmados, nodo.atomos_negados, "Alfa: ∧")
                pila_trabajo.append(nodo.izquierdo)
            elif tipo_elegido == 'NEG_DISJUNCION':
                pendientes_siguientes.extend([f"¬{sub_izq}", f"¬{sub_der}"])
                nodo.izquierdo = NodoArbolSemantico(pendientes_siguientes, nodo.atomos_afirmados, nodo.atomos_negados, "Alfa: ¬∨")
                pila_trabajo.append(nodo.izquierdo)
            elif tipo_elegido == 'NEG_CONDICIONAL':
                pendientes_siguientes.extend([sub_izq, f"¬{sub_der}"])
                nodo.izquierdo = NodoArbolSemantico(pendientes_siguientes, nodo.atomos_afirmados, nodo.atomos_negados, "Alfa: ¬→")
                pila_trabajo.append(nodo.izquierdo)
            elif tipo_elegido == 'NEGACION' and sub_izq.startswith('¬'):
                pendientes_siguientes.append(sub_izq[1:])
                nodo.izquierdo = NodoArbolSemantico(pendientes_siguientes, nodo.atomos_afirmados, nodo.atomos_negados, "Alfa: ¬¬")
                pila_trabajo.append(nodo.izquierdo)

            # REGLAS BETA (2 Ramas)
            elif tipo_elegido == 'DISJUNCION':
                nodo.izquierdo = NodoArbolSemantico(pendientes_siguientes + [sub_izq], nodo.atomos_afirmados, nodo.atomos_negados, "Beta: ∨ (Izq)")
                nodo.derecho = NodoArbolSemantico(pendientes_siguientes + [sub_der], nodo.atomos_afirmados, nodo.atomos_negados, "Beta: ∨ (Der)")
                pila_trabajo.extend([nodo.derecho, nodo.izquierdo])
            elif tipo_elegido == 'CONDICIONAL':
                nodo.izquierdo = NodoArbolSemantico(pendientes_siguientes + [f"¬{sub_izq}"], nodo.atomos_afirmados, nodo.atomos_negados, "Beta: → (Izq)")
                nodo.derecho = NodoArbolSemantico(pendientes_siguientes + [sub_der], nodo.atomos_afirmados, nodo.atomos_negados, "Beta: → (Der)")
                pila_trabajo.extend([nodo.derecho, nodo.izquierdo])
            elif tipo_elegido == 'BICONDICIONAL':
                nodo.izquierdo = NodoArbolSemantico(pendientes_siguientes + [sub_izq, sub_der], nodo.atomos_afirmados, nodo.atomos_negados, "Beta: ↔ (Izq)")
                nodo.derecho = NodoArbolSemantico(pendientes_siguientes + [f"¬{sub_izq}", f"¬{sub_der}"], nodo.atomos_afirmados, nodo.atomos_negados, "Beta: ↔ (Der)")
                pila_trabajo.extend([nodo.derecho, nodo.izquierdo])
            elif tipo_elegido == 'NEG_CONJUNCION':
                nodo.izquierdo = NodoArbolSemantico(pendientes_siguientes + [f"¬{sub_izq}"], nodo.atomos_afirmados, nodo.atomos_negados, "Beta: ¬∧ (Izq)")
                nodo.derecho = NodoArbolSemantico(pendientes_siguientes + [f"¬{sub_der}"], nodo.atomos_afirmados, nodo.atomos_negados, "Beta: ¬∧ (Der)")
                pila_trabajo.extend([nodo.derecho, nodo.izquierdo])
            elif tipo_elegido == 'NEG_BICONDICIONAL':
                nodo.izquierdo = NodoArbolSemantico(pendientes_siguientes + [sub_izq, f"¬{sub_der}"], nodo.atomos_afirmados, nodo.atomos_negados, "Beta: ¬↔ (Izq)")
                nodo.derecho = NodoArbolSemantico(pendientes_siguientes + [f"¬{sub_izq}", sub_der], nodo.atomos_afirmados, nodo.atomos_negados, "Beta: ¬↔ (Der)")
                pila_trabajo.extend([nodo.derecho, nodo.izquierdo])

    def recolectar_modelos(self, nodo):
        if not nodo: return
        if not nodo.izquierdo and not nodo.derecho:
            if not nodo.cerrada:
                modelo = {'afirmados': sorted(list(nodo.atomos_afirmados)), 'negados': sorted(list(nodo.atomos_negados))}
                if modelo not in self.modelos_encontrados: self.modelos_encontrados.append(modelo)
            return
        self.recolectar_modelos(nodo.izquierdo)
        self.recolectar_modelos(nodo.derecho)

    def generar_tabla_verdad_atomos(self, lista_letras):
           """Genera y muestra visualmente la tabla de verdad pura de los átomos detectados."""
           print("\n=== TABLA DE VERDAD DE LOS ÁTOMOS ===")
           letras_ordenadas = sorted(list(lista_letras))
           
           # Encabezado con los nombres de los átomos
           encabezado = " | ".join(letras_ordenadas)
           print(encabezado)
           print("-" * len(encabezado))
           
           # Calcular el número de combinaciones posibles (2^n)
           num_combinaciones = 2 ** len(letras_ordenadas)
           
           for i in range(num_combinaciones):
               valores_fila = []
               for idx in range(len(letras_ordenadas)):
                   # Operación de bits para alternar V y F correctamente por columna
                   valor_bit = (i >> (len(letras_ordenadas) - 1 - idx)) & 1
                   valores_fila.append("V" if valor_bit else "F")
               
               print(" | ".join(valores_fila))
           print("=====================================")     

    def exportar_dot(self, nodo, lineas_dot=None):
        if lineas_dot is None:
            lineas_dot = ["digraph ArbolSemantico {", '  node [shape=box, fontname="Courier", fontsize=10];']
        color = "red" if nodo.cerrada else ("green" if (not nodo.izquierdo and not nodo.derecho) else "black")
        lineas_dot.append(f'  {nodo.id} [label="{nodo.obtener_etiqueta()}", color={color}, penwidth=2];')
        if nodo.izquierdo:
            lineas_dot.append(f'  {nodo.id} -> {nodo.izquierdo.id} [label="{nodo.izquierdo.regla_origen}"];')
            self.exportar_dot(nodo.izquierdo, lineas_dot)
        if nodo.derecho:
            lineas_dot.append(f'  {nodo.id} -> {nodo.derecho.id} [label="{nodo.derecho.regla_origen}"];')
            self.exportar_dot(nodo.derecho, lineas_dot)
        if nodo.id == 1: lineas_dot.append("}")
        return "\n".join(lineas_dot)

    def imprimir_reporte(self, nodo_raiz):
        self.modelos_encontrados = []
        self.recolectar_modelos(nodo_raiz)
        print("\n=== REPORTE DE MODELOS (MUNDOS POSIBLES) ===")
        if not self.modelos_encontrados:
            print("❌ LA BASE DE CONOCIMIENTO ES INCONSISTENTE.")
            print("Todas las ramas contienen contradicciones y se han cerrado (✕).")
        else:
            print(f"✅ LA BASE DE CONOCIMIENTO ES CONSISTENTE. Se encontraron {len(self.modelos_encontrados)} mundos posibles:\n")
            for idx, mod in enumerate(self.modelos_encontrados, 1):
                asignaciones = []
                for a in mod['afirmados']: asignaciones.append(f"{a} = V")
                for n in mod['negados']: asignaciones.append(f"{n} = F")
                print(f"Mundo {idx}: [ {', '.join(asignaciones)} ]")
        print("============================================")
        try:
            with open("arbol_semantico.dot", "w", encoding="utf-8") as f:
                f.write(self.exportar_dot(nodo_raiz))
            print("\n[INFO] Archivo gráfico 'arbol_semantico.dot' exportado con éxito.")
        except Exception: pass

# ==============================================================================
# 5. PARTE: ENTRADA Y ORQUESTACIÓN PRINCIPAL DEL SISTEMA (CON ALMACENAMIENTO)
# ==============================================================================
if __name__ == "__main__":
    print("=========================================================")
    print("  TOKENIZADOR EXPERTO SAT V6.5 (CON ALMAPS)")
    print("=========================================================")
    
    tokenizador = TokenizadorSistemasExpertos()
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
        # RESPUESTA A TU DUDA: Guardado persistente en disco duro
        try:
            with open("base_conocimiento.txt", "w", encoding="utf-8") as archivo_txt:
                for idx, linea in enumerate(lineas_usuario, 1):
                    archivo_txt.write(f"R{idx}: {linea.strip()}\n")
            print("\n[INFO] Base de Conocimiento guardada permanentemente en 'base_conocimiento.txt'.")
        except Exception as e:
            print(f"\n[AVISO] No se pudo escribir el archivo de respaldo: {e}")

        tokenizador.registrar_atomos_de_base(lineas_usuario)
        print("\n=== TABLA DE ÁTOMOS DETECTADOS ===")
        letras_extraidas = set()
        for frase, letra in tokenizador.tabla_atomos.items():
            print(f"{letra} = \"{frase}\"")
            letras_extraidas.add(letra)
            
        formulas_base = []
        print("\n=== BASE DE CONOCIMIENTO TRADUCIDA ===")
        for idx, linea in enumerate(lineas_usuario, 1):
            formula = tokenizador.traducir_oracion(linea)
            formulas_base.append(formula)
            print(f"R{idx}: {linea.strip()}  -->  {formula}")

        print("\n=== SISTEMA EXPERTO INTEGRADO - MOTOR DE INFERENCIA V6.5 ===")
        motor = MotorInferencia()
        nodo_raiz = NodoArbolSemantico(formulas_base)
        print("Procesando árbol semántico iterativo...")
        
        motor.construir_arbol(nodo_raiz)
        
        # Extracción e impresión de la tabla de verdad de átomos limpia
        letras_detectadas = set(tokenizador.tabla_atomos.values())
        motor.generar_tabla_verdad_atomos(letras_detectadas)
        
        motor.imprimir_reporte(nodo_raiz)


   
