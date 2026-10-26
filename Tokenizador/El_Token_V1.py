import re

def limpiar_texto(texto):
    """Limpia el texto de caracteres especiales innecesarios y normaliza espacios."""
    if not texto:
        return ""
    # Quitar signos de puntuación comunes excepto comas intermedias necesarias
    texto_limpio = re.sub(r'[¿?¡!.\"\']', '', texto)
    # Normalizar múltiples espacios a uno solo
    return re.sub(r'\s+', ' ', texto_limpio).strip()

def tokenizar_robusto(oracion):
    oracion = limpiar_texto(oracion)
    
    # Si el usuario ingresó algo vacío o solo espacios
    if not oracion:
        return [], {}

    # Diccionario de conectores soportados
    patrones_conectores = {
        'Y': r'\b(y|pero|además|también|e)\b',
        'O': r'\b(o|u)\b',
        'NO': r'\b(no|ni)\b'
    }

    # --- CASO 1: Estructura Invertida "[Consecuencia] SI [Antecedente]" ---
    match_invertido = re.match(r'^(.+?)\s+si\s+(.+)$', oracion, re.IGNORECASE)
    if match_invertido and not oracion.lower().startswith('si '):
        consecuente_txt = match_invertido.group(1).strip()
        antecedente_txt = match_invertido.group(2).strip()
        
        # Validar que ambas partes contengan texto real antes de procesar
        if antecedente_txt and consecuente_txt:
            tokens_ant, mapa_ant = procesar_bloque_seguro(antecedente_txt, patrones_conectores, {})
            tokens_cons, mapa_total = procesar_bloque_seguro(consecuente_txt, patrones_conectores, mapa_ant)
            
            if tokens_ant and tokens_cons:
                return tokens_ant + [('CONECTOR', '→')] + tokens_cons, mapa_total

    # --- CASO 2: Estructura Normal "SI [Antecedente], [Consecuencia]" ---
    match_normal = re.match(r'^si\s+(.+?),\s*(.+)$', oracion, re.IGNORECASE)
    if match_normal:
        antecedente_txt = match_normal.group(1).strip()
        consecuente_txt = match_normal.group(2).strip()
        
        if antecedente_txt and consecuente_txt:
            tokens_ant, mapa_ant = procesar_bloque_seguro(antecedente_txt, patrones_conectores, {})
            tokens_cons, mapa_total = procesar_bloque_seguro(consecuente_txt, patrones_conectores, mapa_ant)
            
            if tokens_ant and tokens_cons:
                return tokens_ant + [('CONECTOR', '→')] + tokens_cons, mapa_total

    # --- CASO 3: Fallback (Cualquier otra cosa inesperada) ---
    return procesar_bloque_seguro(oracion, patrones_conectores, {})


def procesar_bloque_seguro(texto, patrones, mapa_proposiciones):
    """Segmenta el texto de manera segura tolerando entradas inesperadas."""
    patron_split = '|'.join(f'({patron})' for patron in patrones.values())
    
    # Split seguro manejando excepciones de Regex
    try:
        partes = re.split(patron_split, texto, flags=re.IGNORECASE)
    except Exception:
        partes = [texto]
        
    componentes = [p.strip() for p in partes if p and p.strip()]
    
    tokens = []
    letras_variables = ['p', 'q', 'r', 's', 't', 'u']
    v_index = len(mapa_proposiciones)
    
    for comp in componentes:
        comp_lower = comp.lower()
        
        # Identificar conectores explícitos
        if re.match(patrones['Y'], comp_lower):
            tokens.append(('CONECTOR', '∧'))
        elif re.match(patrones['O'], comp_lower):
            tokens.append(('CONECTOR', '∨'))
        elif re.match(patrones['NO'], comp_lower):
            tokens.append(('CONECTOR', '¬'))
        else:
            # Es texto proposicional. Evitamos agregar conectores huérfanos o basura
            if comp_lower not in mapa_proposiciones:
                if v_index < len(letras_variables):
                    mapa_proposiciones[comp_lower] = letras_variables[v_index]
                else:
                    mapa_proposiciones[comp_lower] = f'p{v_index}'
                v_index += 1
            
            letra = mapa_proposiciones[comp_lower]
            tokens.append(('VARIABLE', letra))
            
    return tokens, mapa_proposiciones


if __name__ == "__main__":
    print("=== Tokenizador SAT Ultra-Robusto ===")
    print("Prueba cualquier entrada (oraciones válidas, texto aleatorio, preguntas...)\n")
    
    entrada = input("Ingresa tu texto: ")
    
    try:
        tokens, diccionario = tokenizar_robusto(entrada)
        
        if not tokens:
            print("\n No se pudo extraer ninguna estructura lógica del texto ingresado.")
        else:
            print("\n[Proposiciones Extraídas]:")
            for texto, letra in diccionario.items():
                print(f"  {letra} = \"{texto}\"")
                
            print("\n[Fórmula SAT Resultante]:")
            formula = " ".join([t[1] for t in tokens])
            print(f"  {formula}")
            
    except Exception as e:
        print(f"\n Ocurrió un error inesperado al procesar la entrada: {e}")
