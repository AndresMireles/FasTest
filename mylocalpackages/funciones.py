# -*- coding: utf-8 -*-

# Importamos el coding utf8 ya que es necesario para las tildes y demás porque si no no lo lee

from bs4 import BeautifulSoup
from random import randint, shuffle
import random
import requests
import pyrebase
import time
import lxml
from math import floor
# Estos paquetes solo se usan en la pregunta de keywords y en principio no funciona por el sklearn creo al subirlo a cloud functions:
# from rake_nltk import Rake
# from sklearn.feature_extraction.text import TfidfVectorizer
# import pandas as pd

# Los paquetes para hacer la request al Java:
from google.oauth2 import service_account
import google.auth.transport.requests
from google.oauth2.service_account import IDTokenCredentials


# Vamos a definir los límites de cada pregunta y los totales:
lim_preg_con_reserva = 12
lim_preg_sin_reserva = 7
lim_total_con_reserva = 35
lim_total_sin_reserva = 20

startTime = time.time()

# Creamos las listas de los archivos que usar:

verbos_lista_url = []
verbos_conjugados_lista_url = []
apellidos_lista_url = []
nombres_propios_lista_url = []
lugares_lista_url = []
stopwords_lista_url = []



# Vamos a definir todas las funciones que vamos a usar en la api:

def leer_archivo_palabras_separadas(texto):
    """
    Esta función nos devuelve una lista donde cada elemento de la lista es una palabra del texto
    """

    # Leemos el archivo por lineas:
    texto_lineas = texto.split("\n")
    lineas_escritas = []
    for linea in texto_lineas:
        if 'página' not in linea.lower() and 'wuolah' not in linea.lower() and 'http' not in linea.lower() and 'ies' not in linea.lower() and 'calle' not in linea.lower() and "www" not in linea.lower() and '.es' not in linea.lower() and '.com' not in linea.lower():
            lineas_escritas.append(linea.strip(
                "\n").replace("_", "").replace("\u200b", ""))

    # Con esta cosa tan tan tan simple quitamos todos los encabezados:
    lineas_limpias = []
    lineas_limpias_aux = []
    for linea in lineas_escritas:
        if linea.lower() not in lineas_limpias_aux:
            lineas_limpias.append(linea)
            lineas_limpias_aux.append(linea.lower())
        else:
            pass

    # Separamos las lineas en palabras:

    palabras_separadas = []
    for linea in lineas_limpias:  # Aquí van lineas_limpias
        palabras_separadas.append(linea.split(" "))

    # Ponemos todo junto en una única lista, es decir, un texto:

    texto_por_palabras = []
    for i in range(len(palabras_separadas)):
        texto_por_palabras.extend(palabras_separadas[i])

    # Ahora vamos a hacer un apaño para que no añada palabras vacías:
    texto_por_palabras_bueno = [
        i.strip("\x0c").strip("\x0c\x0c") for i in texto_por_palabras if i.strip(' ') != "" and i.replace(' ', "") != " " and i.replace(' ', "") != "_"]

    return texto_por_palabras_bueno


def leer_archivo_parrafos(texto):
    """
    Esta función nos devuelve una lista del texto separado por párrafos
    """

    texto_parrafos = texto.split('\n\n')

    texto_parrafos_bueno = []

    for parrafo in texto_parrafos:
        if parrafo != "" and parrafo != " " and len(parrafo.replace(" ", "")) > 10 and 'página' not in parrafo.lower() and 'wuolah' not in parrafo.lower() and "www" not in parrafo.lower() and '.es' not in parrafo.lower() and '.com' not in parrafo.lower():
            texto_parrafos_bueno.append(parrafo)

    return texto_parrafos_bueno


def leer_archivo_str(texto):
    """
    Esta función nos devuelve un texto como una única string
    """
    texto_por_palabras = leer_archivo_palabras_separadas(
        texto)

    # Convertimos el texto a string:

    texto_str = " ".join(texto_por_palabras)

    return texto_str


def leer_archivo_dict_de_frases_separadas(texto):
    """
    Esta función nos devuelve un diccionario con el par keyword(numero de frase)-value(la frase como una lista de strings)
    """
    texto_por_palabras = leer_archivo_palabras_separadas(
        texto)

   # Separamos por frases, creando un diccionario con el par keyword(numero de frase)-value(la frase):

    frases_separadas_dict = {1: []}
    frase = 1
    for palabra in texto_por_palabras:
        if not palabra.endswith(".") and not palabra.endswith("!") and not palabra.endswith("?"):
            if palabra != " " and palabra != "":  # Hacemos este apaño para que no meta palabras vacías
                frases_separadas_dict[frase].append(palabra)
        else:
            if palabra != " " and palabra != "":
                # Si solo tiene longitud 1 la palabra seguramente será algo rollo a.C. y no queremos hacer otra frase:
                if len(palabra) == 2:
                    frases_separadas_dict[frase].append(palabra)
                else:
                    frases_separadas_dict[frase].append(palabra)
                    frase += 1
                    frases_separadas_dict[frase] = []

    # Hacemos un pequeño ajuste ya que siempre sobra una fila vacía:
    frases_separadas_dict.pop(frase)

    return frases_separadas_dict


def leer_archivo_dict_de_frases_str(texto):
    """
    Esta función nos devuelve un diccionario con el par keyword(número de frase)-value(frase como string)
    """
    frases_dict_separadas = leer_archivo_dict_de_frases_separadas(texto)

    # Simplemente hacemos un join para que cada value sea un str con toda la frase:

    dict_frases_str = {}
    for key, value in frases_dict_separadas.items():
        dict_frases_str[key] = " ".join(value)

    return dict_frases_str


def leer_archivo_lista_de_listas(texto):
    """
    Esta función nos devuelve una lista de listas con cada lista de listas una frase cuyos elementos son strings de cada palabra
    """
    frases_separadas_dict = leer_archivo_dict_de_frases_separadas(texto)

    # Convertimos el diccionario a una lista de listas:

    frases_separadas_lista = []
    for frase in frases_separadas_dict:
        frases_separadas_lista.append(frases_separadas_dict[frase])

    return frases_separadas_lista


def leer_archivo_lista_de_strings(texto):
    """
    Esta función nos devuelve una lista donde cada elemento son cada frase como una única string (cada frase es una string diferente)
    """
    frases_separadas_lista = leer_archivo_lista_de_listas(texto)

    # Ahora lo convertimos a una lista de strings ya que nos es útil para algunas cosas:

    frases_en_string = []
    for frase in frases_separadas_lista:
        frases_en_string.append(" ".join(frase))

    return frases_en_string


# La función para coger el texto y separar por páginas de un xml:

def archivo_a_texto(texto, tags=False, lista=[], borrar=True):

    # Parsing the document in xml form and selecting content only
    text_xml = texto

    # Creating a BeautifulSoup object to parse the xml
    soup = BeautifulSoup(text_xml, features='lxml')

    # Deleting annotations
    lepra = soup.findAll("div", {"class": "annotation"})
    pp = soup.findAll("p")
    llavee = [repr('R\ne\n'), repr('se\nrv\n'), repr('a\nd\n'),
              repr('o\ns \n'), repr('to\nd\n'), repr(
                  'o\ns \n'), repr('lo\ns \n'),
              repr('d\ne\n'), repr('re\nch\n'), repr(
                  'o\ns.\n'), repr(' N\no\n'),
              repr(' s\ne\n'), repr(' p\ne\n'), repr(
                  ' p\ne\n'), repr('rm\nit\n'),
              repr('e\n la\n'), repr(' e\nxp\n'), repr(
                  'lo\nta\n'), repr('ci\nó\n'),
              repr('n\n e\n'), repr('co\nn\n'), repr(
                  'ó\nm\n'), repr('ic\na\n'),
              repr(' n\ni l\n'), repr('a\n t\n'), repr(
                  'ra\nn\n'), repr('sf\no\n'),
              repr('rm\na\n'), repr('ci\nó\n'), repr(
                  'n\n d\n'), repr('e\n e\n'),
              repr('st\na\n'), repr(' o\nb\n'), repr(
                  'ra\n. Q\n'), repr('u\ne\n'),
              repr('d\na\n'), repr(' p\ne\n'), repr(
                  'rm\nit\n'), repr('id\na\n'),
              repr(' la\n im\n'), repr('p\nre\n'), repr(
                  'si\nó\n'), repr('n\n e\n'),
              repr('n\n s\n'), repr('u\n t\n'), repr(
                  'o\nta\n'), repr('lid\na\n'),
              repr('d\n.\n')]
    for i in lepra:

        i.decompose()

    for i in pp:

        texto = i.text
        raw_text = repr(texto)

        if raw_text in llavee:

            i.decompose()
            """
            # first filter to possibly become removed
            try:
                int(i)
                print("Not deleted it was an int ")
            except:
                try:
                    float(i)
                    print("Not deleted it was a float")
                except:
                    i.decompose()
            """

    # In order to choose only the text we first try to find if
    # it is divided by pages
    pages = soup.findAll("div", {"class": "page"})

    # if we found page division we only take the content in the pages from xml
    if len(pages) > 0:

        # print("Page division found!")

        # First we delete 1 to every element in the giving list
        # to update it to the python indexing
        if lista:
            lista = [x-1 for x in lista]

            # now we have to iterate through the given pages to delete
            # and using the index they have we delete the element with the
            # same index from the pages

            # Actualizing parameter
            equi = 0

            if borrar:

                for i in range(0, len(pages)):

                    if i in lista:
                        pages.pop(i - equi)
                        equi += 1

            # When we want to choose pages and not delete
            elif not borrar:

                # list with the positions of all the pages in xml
                totals = list(range(0, len(pages)))

                # from this list we delete all the elements to choose
                # so we have now a list that we will use to delete the remaining
                # pages from the xml-pags
                for i in range(0, len(lista)):

                    totals.remove(lista[i])

                requi = 0
                for i in range(0, len(pages)):

                    if i in totals:
                        pages.pop(i - requi)
                        requi += 1

        if tags:
            return [pages, len(pages)]

        elif not tags:

            text_pags = ""
            for pagina in pages:

                text_pags += ""
                text_pags += pagina.text

                # text_pags += "\n"

            return [text_pags, len(pages)]

    # if we didnt find any page division we would return everythin except meta data
    elif len(pages) <= 0:

        print("Page structure not found :(")
        text_sinpags = soup.findAll("p")
        texto_alter = ""

        if tags:

            return [text_sinpags, len(pages)]

        elif not tags:

            for i in text_sinpags:

                texto_alter += i.text
                texto_alter += "\n"

            return [texto_alter, len(pages)]

# La pregunta de rellenar keywords:


def plan_1_buscar_n_frases_importantes(texto, n=None):
    """
    Esta función devuelve las n frases más importantes de un texto.

    *Argumentos*:
    ----------------------
    texto : str, el texto del que buscar las frases.

    n : int, el máximo número de frases que escoger (por defecto es la mitad de las frases del archivo).

    """

    #                                               Primera parte

    # Lo primero que hacemos es cargar nuestro texto con las frases como strings y como una string única ya que son las formas en las que lo vamos a necesitar
    frases_en_str = leer_archivo_lista_de_strings(
        texto)

    texto_en_str = leer_archivo_str(texto)

    # Ahora buscamos las frases más importantes con Rake. Más o menos está bien que por cada texto coja la mitad de las frases ya que Rake tiene un pequño fallo y
    # es que coge a veces, por ejemplo, dos frases que considera de las más importantes del texto dentro de una misma oración (separada por .) por lo que
    # en verdad cogerá menos frases de las que le ponemos que coja

    stopwords = stopwords_lista_url

    rakee = Rake(stopwords=stopwords, language="spanish")

    rakee.extract_keywords_from_text(texto_en_str)

    # El número de frases, si el usuario no ha especificado un número de frases, es la mitad de las frases totales del texto:

    n_frases = 0

    if n == None:
        n_frases = len(frases_en_str)//2
    else:
        n_frases = n

    frases_importantes_incompletas = rakee.get_ranked_phrases_with_scores()[
        :n_frases]

    # Como las frases que da no son las frases completas hay que buscar esas frases dentro de todo el texto

    frases_incompletas = [frase[1] for frase in frases_importantes_incompletas]

    frases_importantes = {}

    for i in range(len(frases_incompletas)):
        for j in range(len(frases_en_str)):

            if frases_incompletas[i].lower() in frases_en_str[j].lower():
                frases_importantes[j+1] = frases_en_str[j]

    return frases_importantes


def plan_1_buscar_palabras_importantes(texto):
    """
    Esta función devuelve la palabra más importante de cada frase del texto.

    *Argumentos*:
     ----------------------
    texto : str, el archivo del que dar las frases.

    """

    #                                               Segunda parte

    # Lo primero que hacemos es cargar nuestro texto con las frases como strings

    frases_en_str = leer_archivo_lista_de_strings(
        texto)

    # Ahora, una vez ya hemos seleccionado las frases más importantes del texto tenemos que seleccionar las palabras más importantes de cada frase.
    # Esto lo haremos con el TF-IDF

    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(frases_en_str)
    names = vectorizer.get_feature_names()
    data = vectors.todense().tolist()

    # Hacemos un dataframe con cada fila una frase y cada columna una palabra
    df = pd.DataFrame(data, columns=names)

    # Filtramos las stopwords

    st = stopwords_lista_url

    # Con esto eliminamos las stopwords:
    df = df[filter(lambda x: x not in st, df.columns)]

    # Ahora almacenamos en un diccionario cada frase con su palabra más importante
    # (omito el valor que aporta cada palabra a cada frase ya que nos es irrelevante)

    contador = 1
    palabras_importantes = {}
    for i in df.iterrows():
        palabra = i[1].sort_values(ascending=False)[:1].to_dict()
        palabras_importantes[f"frase_{contador}"] = "".join([
            key for key, value in palabra.items()])

        contador += 1

    # print(palabras_importantes)

    return palabras_importantes


def plan_1_frases_con_palabras_importantes(texto, n=None, n_frase=True):
    """
    Esta función devuelve las n frases más importantes del texto junto con la palabra más importante de cada frase.

    *Argumentos*:
    ----------------------
    texto : str, el archivo del que dar las frases.

    n : int, el máximo número de frases que escoger (por defecto es la mitad de las frases del archivo).

    n_frase: boolean, si True devuelve las frases con el número de cada frase dentro del texto, si False, no lo hace.

    """

    #                                               Tercera parte

    # Una vez ya tenemos las frases más importantes del texto, vamos a poner cada frase con su palabra más
    # importante en un diccionario para tenerlo más ordenado y poder trabajar con ello mejor

    # Primero tenemos que marcar el número de frases que queremos. El número de frases, si el usuario
    # no ha especificado un número de frases, es la mitad de las frases totales del texto:

    frases_en_str = leer_archivo_lista_de_strings(
        texto)

    n_frases = 0

    if n == None:
        n_frases = len(frases_en_str)//2
    else:
        n_frases = n

    # Cargamos las frases y palabras importantes:

    palabras_importantes = plan_1_buscar_palabras_importantes(texto)
    frases_importantes = plan_1_buscar_n_frases_importantes(
        texto, n_frases)

    # Primero me interesa tener alamcenada una lista con las frases que están dentro de las frases importantes:

    numeros_frases = list(frases_importantes.keys())
    numeros_palabras = list(palabras_importantes.keys())

    # Una vez ya los tenemos, hacemos un diccionario con el value de cada keyword una lista con el número de frase, la frase y la palabra más importante

    frases_con_palabras_importantes = {}
    contador = 1

    if n_frase:
        for key in numeros_frases:
            # Hacemos un ajuste para que no ponga frases repetidas:
            if frases_importantes[key] not in [value[2] for value in list(frases_con_palabras_importantes.values())]:
                if str(f"frase_{key}") in numeros_palabras:
                    frases_con_palabras_importantes[contador] = [str(f"frase_{key}"),
                                                                 frases_importantes[key], palabras_importantes[str(f"frase_{key}")]]
                    contador += 1
    else:
        for key in numeros_frases:
            # Hacemos un ajuste para que no ponga frases repetidas:
            if frases_importantes[key] not in [value[1] for value in list(frases_con_palabras_importantes.values())]:
                # Cuidado que aquí es value[1] y no value[2] porque cambia la longitud de cada lista dentro de frases_con_palabras_importantes
                if str(f"frase_{key}") in numeros_palabras:
                    frases_con_palabras_importantes[contador] = [
                        frases_importantes[key], palabras_importantes[str(f"frase_{key}")]]
                    contador += 1

    return frases_con_palabras_importantes


def preguntas_rellenar_keywords(texto):

    # Esta función sirve para quitar los acentos a una palabra y la necesitamos para que las respuestas no dependan de una tilde

    # def normalize(word):
    #     replacements = (
    #         ("á", "a"),
    #         ("é", "e"),
    #         ("í", "i"),
    #         ("ó", "o"),
    #         ("ú", "u"),
    #     )
    #     for a, b in replacements:
    #         word = word.replace(a, b).replace(a.upper(), b.upper())
    #     return word

    # Vamos a guardar la lista de verbos para que si la palabra es un verbo no la ponga como keyword:
    lista_verbos = [verbo.replace(" ", "") for verbo in verbos_lista_url]

    lista_verbos_conjugados = [verbo.replace(
        " ", "") for verbo in verbos_conjugados_lista_url]

    # Primero extraemos nuestras keyphrases para hacer las preguntas

    keyphrases = plan_1_frases_con_palabras_importantes(
        texto, n_frase=False)

    frases_pregunta = {}
    keywords_preguntas = []
    keyfrases_preguntas = []
    contador = 1
    # Vamos a ponerle un máximo de preguntas. De momento ponemos 30 como máximo para que si el test solo
    # saca preguntas de rellenar keywords pueda tener un test con 20 preguntas y 10 de recambio:
    maxNum = 20
    for frase in range(1, len(keyphrases)+1):
        if len(frases_pregunta.keys()) < maxNum:
            keyphrase = keyphrases[frase][0]
            # Quitamos el .lower()
            keyword = keyphrases[frase][1].strip('').replace(" ", "").replace("_", "").replace("…", "").replace("-", "").replace(")", "").replace("≪", "").replace("«", "").replace("»", "").replace(
                "(", "").replace("", "").replace("/", "").replace("...", "").replace(".", "").replace(",", "").replace("'", "").replace('"', "").replace(":", "").replace(";", "").replace("?", "").replace("!", "").replace('“', "").replace("”", "")

            # Sustituimos las keywords en nuestra frase por un __ de igual longitud que la palabra.
            # Vamos a intentar cambiar de tres formas posibles: en minúsuculas, en mayúsculas y con capital letter:
            if keyword.lower() in keyphrase:
                if len(keyword) > 4:
                    frase_modificada = keyphrase.replace(
                        keyword.lower(), "_"*len(keyword))
                else:
                    if keyphrase[(keyphrase.index(keyword.lower())-1)] == " " and keyphrase[keyphrase.index(keyword.lower())+len(keyword.lower())] == " ":
                        frase_modificada = keyphrase.replace(
                            keyword.lower(), "_"*len(keyword))

            if keyword.upper() in keyphrase:
                if len(keyword) > 4:
                    frase_modificada = keyphrase.replace(
                        keyword.upper(), "_"*len(keyword))
                else:
                    if keyphrase[(keyphrase.index(keyword.upper())-1)] == " " and keyphrase[keyphrase.index(keyword.upper())+len(keyword.upper())] == " ":
                        frase_modificada = keyphrase.replace(
                            keyword.upper(), "_"*len(keyword))

            if keyword.capitalize() in keyphrase:
                if len(keyword) > 4:
                    frase_modificada = keyphrase.replace(
                        keyword.capitalize(), "_"*len(keyword))
                else:
                    if keyphrase[(keyphrase.index(keyword.capitalize())-1)] == " " and keyphrase[keyphrase.index(keyword.capitalize())+len(keyword.capitalize())] == " ":
                        frase_modificada = keyphrase.replace(
                            keyword.capitalize(), "_"*len(keyword))

            # Ponemos que no sea verbo ni adverbio, que no sea ni muy larga ni muy corta y que no esté ya la keyword o la frase:
            if keyword not in lista_verbos and keyword not in lista_verbos_conjugados and 4 < len(keyword) < 20 and 60 < len(frase_modificada) < 250 and not keyword.endswith('mente') and not keyword == '000' and not keyword == '00' and not keyword == '0' and keyword not in keywords_preguntas and frase_modificada not in keyfrases_preguntas and keyphrase.find(keyword) != 0:
                frases_pregunta[contador] = [keyword, frase_modificada]
                keywords_preguntas.append(keyword)
                keyfrases_preguntas.append(frase_modificada)
                contador += 1

    return frases_pregunta


# La pregunta de enumeraciones:

def preguntas_enumeraciones(texto):

    guiones = ['-', '*', '.-', '1)', '2)', '3)', '4)', '5)', '6)',  'i)', 'ii)', 'iii)', 'iv)', "1-.", "2-.", "3-.",
               'I.', 'II.', 'III.', 'IV.', '', 'a)', 'b)', 'c)', 'd)', '·',
               'A.', 'B.', 'C.', 'D.', '1.', '2.', '3.', '4.',
               '', '1º', '2º', '3º', '4º', '1º)', '2º)', '3º)', '4º)', 'A)', 'B)', 'C)',
               '•', "\u00A4", "\u2022", "\u2023", "\u2218", "\u2219", "\u22C4", "\u22C5",
               "\u22C6", "\u2311",  "\u2318", "\u2317",  "\u23F5", "\u25A0", "\u25A1",
               "\u25A3", "\u25AA", "\u25AB", "\u25B2", "\u25B4", "\u25B8", "\u25BA", "\u25CB",
               "\u25CF", "\u25E6", "\u25FB", "\u25FD", "\u25FE", "\u2662", "\u2666", "\u2756",
               "\u00B0", "\u220E", "\u23Fa", "\u23F9", "\u2597", "\u2596", "\u25FC",
               "\u26AB", "\u26AC", "\u2981", "\u29EB", "\u2BC0", "\u2E30", "\uA537",
               "\uF0B7", "\uF0A7", "\uF0B7", "\uF02D", "\uF0FB", "\uF0B7", "o", "◦"
               ]

    # numeros = ['1)', '2)', '3)', '4)', '5)', '6)']
    # romanos = ['I.', 'II.', 'III.', 'IV.']
    # romans = ['i)', 'ii)', 'iii)', 'iv)']

    diccionario_enum = {}
    counter = 0
    contador_posicion = 0
    key = 1
    pasar = False
    # lista_patron_actual = []
    # salir_patrones = False

    lineas = texto.split("\n")
    lineas[:] = [x for x in lineas if not (
        x.replace("\\n", "") == "" or len(x.replace("\\n", "")) < 6)]

    # Loop to iterate through the lines of the text to see if that line starts with one
    # of the marks in guiones we takes it as one enumerations
    diccionario_enum[key] = []
    for sentence in lineas:

        if pasar:
            counter += 1

        if counter >= 5:
            pasar = False
            counter = 0
            key += 1
            diccionario_enum[key] = []

        # Iterating through all the characters in the list of guiones
        complete = 0
        for begin in guiones:

            complete += 1
            # WE found an app that was
            if sentence.replace(" ", "").replace("\\n", "").startswith(begin) and sentence.replace(" ", "").replace("\\n", "")[len(begin)].isupper():
                counter = 0
                pasar = True

                if len(diccionario_enum[key]) == 0:

                    guia_actual = begin

                if begin == guia_actual:

                    diccionario_enum[key].append(sentence)
                    break

                elif begin != guia_actual:

                    key += 1
                    diccionario_enum[key] = []

                    # if lineas[contador_posicion - 1].endswith(":") and len(lineas[contador_posicion-1].split(".")) > 0:
                    #     diccionario_enum.append(
                    #         lineas[contador_posicion-1].split(".")[-1])
                    # elif lineas[contador_posicion - 1].endswith(":") and len(lineas[contador_posicion-1].split(".")) == 0:
                    #     if len(lineas[contador_posicion-2].split(".")) > 0:
                    #         frase = lineas[contador_posicion-1] + \
                    #             lineas[contador_posicion-2].split(".")[-1]
                    #         diccionario_enum.append(frase)
                    diccionario_enum[key].append(sentence)

                    break

                break

            elif sentence.replace(" ", "").replace("\\n", "").endswith(":"):

                pasar = False
                counter = 0
                key += 1
                diccionario_enum[key] = []
                break

        # We have dividied the list of beginnings into smaller lists to couple all the patterns followed
        # We check if the element is a list and we iterate through it

        if complete == len(guiones) and pasar:

            diccionario_enum[key][-1] += sentence + " "

        contador_posicion += 1
    diccionario_corregido = {}
    i = 0
    frase_aux = ""

    for key in diccionario_enum.keys():
        if len(diccionario_enum[key]) > 0:

            for frase in diccionario_enum[key][-1].split("."):
                frase_aux += frase

                if len(frase_aux) > 10:

                    diccionario_enum[key][-1] = frase_aux
                    frase_aux = ""
                    break

        if len(diccionario_enum[key]) > 1:
            diccionario_corregido[i] = diccionario_enum[key]
            i += 1

    copia_corregido = {}

    diccionario_preguntas = {}
    diccionario_preguntas_enumers = {}
    keys_preg = 0
    dicc_fin = 0

    for key in diccionario_corregido.keys():
        copia_corregido[key] = diccionario_corregido[key]

    for key in diccionario_corregido.keys():

        if len(diccionario_corregido[key]) > 1:

            rango = len(diccionario_corregido[key]) - 2
            valor_elegido = randint(0, rango)
            chosen_frase = diccionario_corregido[key][valor_elegido]
            diccionario_corregido[key].pop(valor_elegido)

            if ":" in chosen_frase:

                division_dos = chosen_frase.split(":")

                concepto = division_dos[0].split(" ")
                max_palabras = 4
                for ele in concepto:
                    if ele in guiones:
                        max_palabras += 1

                if len(concepto) <= max_palabras:

                    # print(division_dos[0])
                    # print("_"*20)
                    keys_preg += 1
                    definicion = division_dos[1].split(".")[0]

                    for i in range(0, len(division_dos[1].split(".")) - 1):
                        if len(definicion.split(" ")[-1]) <= 3:
                            definicion += division_dos[1].split(".")[i+1]
                        elif len(definicion.split(" ")[-1]) > 3:
                            break

                    diccionario_preguntas[keys_preg] = []
                    if definicion != "":
                        if definicion[0] == " ":
                            definicion = definicion[1:]
                    definicion = "_"*10 + ": " + definicion.strip(" ")+"."
                    correct = " ".join(division_dos[0].split(" ")[1:])
                    diccionario_preguntas[keys_preg].append(
                        correct.capitalize())
                    diccionario_preguntas[keys_preg].append(definicion)

                    opciones = []
                    if len(correct) <= 4 or correct.lower() == "ejemplo" or correct.lower() == "ejemplos" or correct.lower() == "ej" or correct.lower() == "ejs":
                        continue

                    opciones.append(correct.capitalize())
                    counter = 0

                    for frases_restantes in diccionario_corregido[key]:

                        counter += 1

                        divide_for_options = frases_restantes.split(":")

                        concepto = divide_for_options[0].split(" ")
                        max_palabras2 = 4
                        for ele in concepto:
                            if ele in guiones:
                                max_palabras2 += 1

                        if len(divide_for_options[0].split(" ")) <= max_palabras2:

                            incorrect = " ".join(
                                divide_for_options[0].split(" ")[1:])
                            if (len(incorrect.split(" ")) < 5):
                                opciones.append(incorrect.capitalize())

                        if counter == 2:

                            if len(opciones) > 1:
                                shuffle(opciones)
                                dicc_fin += 1
                                diccionario_preguntas[keys_preg].append(
                                    opciones)
                                if len(diccionario_preguntas[keys_preg]) == 3 and len(diccionario_preguntas[keys_preg][1].replace(" ", "")) > 10 and len(diccionario_preguntas[keys_preg][1].split(" ")) > 3:
                                    diccionario_preguntas_enumers.__setitem__(
                                        str(dicc_fin), diccionario_preguntas[keys_preg])
                                break
                            # elif len(diccionario_preguntas[keys_preg]) <=2:
                            #     diccionario_preguntas.pop(keys_preg)
                            #     keys_preg -= 1
                            #     break

            # elif "." in chosen_frase:

            #     pass

    return diccionario_preguntas_enumers


# La pregunta de nombres propios:

def preguntas_nombres_propios(texto, idioma):

    # -*- coding: utf-8 -*-
    # hacemos una lista con nombres propios en español
    nombres_1 = []  # Lista con nombres provisional
    lim_preguntas = 2  # Numero maximo de preguntas con la misma respuesta+
    stopwords = []

    # Leemos el archivo txt de los nombres y los metemos en una lista
    nombres_1 = [nombre.replace(" ", "")
                 for nombre in nombres_propios_lista_url]

    # Leemos el archivo de stopwords:
    stopwords = [stopword.replace(" ", "")
                 for stopword in stopwords_lista_url]

    # Abrimos el texto a analizar primero en una lista de palabras separadas y en un diccionario con la keyword siendo
    # el número de frase y el value la frase.

    texto_palabras_puntos = leer_archivo_palabras_separadas(texto)
    texto_diccionario = leer_archivo_dict_de_frases_str(
        texto)
    texto_frases = leer_archivo_lista_de_strings(
        texto)

    # Creamos las listas con las que quitar del texto las frases que hemos usado para pasárselo sin esas frases a la siguiente pregunta:
    texto_frases_siguiente = [frase for frase in texto_frases]
    # Este dict contiene cada key la frase del texto con el ____ replace y cada value es la frase sin eso:
    texto_frases_aux = {}

    texto_palabras = []
    nombres_texto = []
    nombres_texto_1 = []
    nombres_texto_incompleto = []
    frases_sin_mierda = []
    nombres = []

    # Limpiamos las palabras y los nombres de puntos y espacios para que no haya errores de reconocimiento.
    for palabra in texto_palabras_puntos:
        palabra_sin = palabra.replace(" ", "").replace("¿", "").replace("¡", "").replace("_", "").replace("…", "").replace("-", "").replace(")", "").replace("...", "").replace(
            "(", "").replace("", "").replace("/", "").replace(".", "").replace("≪", "").replace("«", "").replace("»", "").replace(",", "").replace("'", "").replace('"', "").replace(":", "").replace(";", "").replace("?", "").replace("!", "").replace('“', "").replace("”", "").replace("\u00A4", "").replace("\u2022", "").replace("\u2023", "").replace("\u2218", "").replace("\u2219", "").replace("\u22C4", "").replace("\u22C5", "").replace("\u22C6", "").replace("\u2311", "").replace("\u2318", "").replace("\u2317", "").replace("\u23F5", "").replace("\u25A0", "").replace("\u25A1", "").replace("\u25A3", "").replace("\u25AA", "").replace("\u25AB", "").replace("\u25B2", "").replace("\u25B4", "").replace("\u25B8", "").replace("\u25BA", "").replace("\u25CB", "").replace("\u25CF", "").replace("\u25E6", "").replace("\u25FB", "").replace("\u25FD", "").replace("\u25FE", "").replace("\u2662", "").replace("\u2666", "").replace("\u2756", "")

        texto_palabras.append(palabra_sin)
    for frase in texto_diccionario.values():
        frase = frase.replace("_", "").replace("¿", "").replace("¡", "").replace("-", "").replace(")", "").replace("…", "").replace("...", "").replace(
            "(", "").replace("", "").replace("/", "").replace(".", "").replace(",", "").replace("≪", "").replace("«", "").replace("»", "").replace("'", "").replace('"', "").replace(":", "").replace(";", "").replace("?", "").replace("!", "").replace('“', "").replace("”", "").replace("\u00A4", "").replace("\u2022", "").replace("\u2023", "").replace("\u2218", "").replace("\u2219", "").replace("\u22C4", "").replace("\u22C5", "").replace("\u22C6", "").replace("\u2311", "").replace("\u2318", "").replace("\u2317", "").replace("\u23F5", "").replace("\u25A0", "").replace("\u25A1", "").replace("\u25A3", "").replace("\u25AA", "").replace("\u25AB", "").replace("\u25B2", "").replace("\u25B4", "").replace("\u25B8", "").replace("\u25BA", "").replace("\u25CB", "").replace("\u25CF", "").replace("\u25E6", "").replace("\u25FB", "").replace("\u25FD", "").replace("\u25FE", "").replace("\u2662", "").replace("\u2666", "").replace("\u2756", "")
        frases_sin_mierda.append(frase)

    lista_valores_indeseados = [".", "?", "!", "¿", "¡",
                                ")", ":", ";", "·", "<", ">", "-", "'", '"', '“', "”", "...", "≪", "«", "»", "…", "\u00A4", "\u2022", "\u2023", "\u2218", "\u2219", "\u22C4", "\u22C5",
                                "\u22C6", "\u2311",  "\u2318", "\u2317",  "\u23F5", "\u25A0", "\u25A1",
                                "\u25A3", "\u25AA", "\u25AB", "\u25B2", "\u25B4", "\u25B8", "\u25BA", "\u25CB",
                                "\u25CF", "\u25E6", "\u25FB", "\u25FD", "\u25FE", "\u2662", "\u2666", "\u2756"]
    for nombre in nombres_1:
        nombre_sin = nombre.replace(" ", "")
        if nombre_sin[-1] in lista_valores_indeseados:
            nombre_sin = nombre_sin[:-1]

        nombres.append(nombre_sin)

    if len(nombres) > 859:
        nombres_masc = nombres[0:859]
    else:
        nombres_masc = nombres
    nombres_bakanos = nombres[0:126]

    for palabra in texto_palabras:
        if palabra in nombres:
            nombres_texto_incompleto.append(palabra)

    nombres_texto_masc_1 = []
    nombres_texto_fem_1 = []
    nombres_texto_fem_incompleto = []
    nombres_texto_masc_incompleto = []
    nombres_texto_fem = []
    nombres_texto_masc = []
    for nombre in nombres_texto_incompleto:
        if nombre in nombres_masc:
            nombres_texto_masc_incompleto.append(nombre)
        else:
            nombres_texto_fem_incompleto.append(nombre)
    # es porque mira la siguiente palabra del Luis que encuentra primero, por eso cuando hay más de uno pilla la primera palabra del primero

    # Comprobamos si hay nombres en el texto y los guardamos en una lista que se llama nombres_texto
    # nombres_texto_incompleto = list(set(nombres_texto_incompleto))
    # print(texto_palabras_puntos[texto_palabras.index("José")])
    for nombre in nombres_texto_incompleto:
        for palabra in texto_palabras:
            if palabra == nombre:
                nombre_completo = nombre
                for i in range(1, 3):
                    if "." in texto_palabras_puntos[texto_palabras.index(nombre)] or "," in texto_palabras_puntos[texto_palabras.index(nombre)]:

                        break
                    if texto_palabras[texto_palabras.index(nombre)+1] == "de" or texto_palabras[texto_palabras.index(nombre)+1] == "el" or texto_palabras[texto_palabras.index(nombre)+1] == "del" or texto_palabras[texto_palabras.index(nombre)+1] == "la":
                        if texto_palabras[texto_palabras.index(nombre)+2][0].isupper():
                            nombre_completo = nombre+" "+texto_palabras[texto_palabras.index(
                                nombre)+1]+" "+texto_palabras[texto_palabras.index(nombre)+2]
                        break

                    try:

                        if len(texto_palabras[texto_palabras.index(nombre)+i]) > 0 and texto_palabras[texto_palabras.index(nombre)+i][0].isupper() and texto_palabras[texto_palabras.index(nombre)+i].lower() not in stopwords:
                            # Ponemos una condición para que no coja si todo es mayúsculas pero distinguiendo cuando es Alfonso VII por ejemplo.
                            if len(texto_palabras[texto_palabras.index(nombre)+i]) >= 4 and not texto_palabras[texto_palabras.index(nombre)+i][1].isupper():
                                siguiente = texto_palabras[texto_palabras.index(
                                    nombre)+i]

                                nombre_completo += " " + siguiente
                                if (".") in texto_palabras_puntos[texto_palabras.index(nombre)+i] or (",") in texto_palabras_puntos[texto_palabras.index(nombre)+i]:
                                    break
                            if len(texto_palabras[texto_palabras.index(nombre)+i]) < 5:
                                siguiente = texto_palabras[texto_palabras.index(

                                    nombre)+i]

                                nombre_completo += " " + siguiente
                                if (".") in texto_palabras_puntos[texto_palabras.index(nombre)+i] or (",") in texto_palabras_puntos[texto_palabras.index(nombre)+i]:
                                    break
                        else:
                            break
                    except:
                        pass
                nombres_texto_1.append(nombre_completo)
                try:
                    texto_palabras.replace(nombre, " ", 1)
                except:
                    pass

                if nombre in nombres_texto_masc_incompleto:
                    nombres_texto_masc.append(nombre_completo)
                if nombre in nombres_texto_fem_incompleto:
                    nombres_texto_fem.append(nombre_completo)

    for nombre in nombres_texto_1:
        nombre_sin_punto = nombre.replace(".", "")
        if nombre_sin_punto[len(nombre_sin_punto)-1] == " ":
            nombre_sin_espacio = nombre_sin_punto[:-1]
        else:
            nombre_sin_espacio = nombre_sin_punto
        nombres_texto.append(nombre_sin_espacio)
        if nombre in nombres_texto_masc_1:
            nombres_texto_masc.append(nombre_sin_espacio)
        if nombre in nombres_texto_fem_1:
            nombres_texto_fem.append(nombre_sin_espacio)

    nombres_texto = list(set(nombres_texto))
    nombres_texto_masc = list(set(nombres_texto_masc))
    nombres_texto_fem = list(set(nombres_texto_fem))
    for nombre in nombres_texto:
        if len(nombre.split()) == 1 and nombre not in nombres_bakanos:
            nombres_texto.remove(nombre)
    for nombre in nombres_texto_masc:
        if len(nombre.split()) == 1 and nombre not in nombres_bakanos:
            nombres_texto_masc.remove(nombre)
    for nombre in nombres_texto_fem:
        if len(nombre.split()) == 1 and nombre not in nombres_bakanos:
            nombres_texto_fem.remove(nombre)

    # Ahora vamos a quitar los nombres que haya en plan Alberti y Rafael Alberti:
    nombres_texto_aux = []
    for nombre in nombres_texto:
        nombres_texto_aux.append(nombre)

    for nombre in nombres_texto:
        nombres_texto_aux.remove(nombre)
        for nombre2 in nombres_texto_aux:
            if nombre.replace(' ', "") in nombre2.replace(' ', ""):
                # print("nombre  (quitado) "+nombre)
                try:
                    nombres_texto.remove(nombre)
                    if nombre in nombres_texto_masc:
                        nombres_texto_masc.remove(nombre)
                    if nombre in nombres_texto_fem:
                        nombres_texto_fem.remove(nombre)

                except:
                    pass
            if nombre2.replace(' ', "") in nombre.replace(' ', ""):
                # print("nombre "+nombre)
                # print("nombre2 (quitado)  "+nombre2)
                try:
                    nombres_texto.remove(nombre2)
                    if nombre2 in nombres_texto_masc:
                        nombres_texto_masc.remove(nombre2)
                    if nombre2 in nombres_texto_fem:
                        nombres_texto_fem.remove(nombre2)
                except:
                    pass

    # Creamos una lista en la que metemos las frases que contienen nombres con ________ ya sustituido.
    lista_preguntas_1 = []
    # Creamos un diccionario que tambien contiene estas frases pero que además su value es la respuesta correcta.
    dic_preguntas_respuestas = {}

    # La lista para hacer que no se haga más de una pregunta de la misma frase:
    lista_frases_usadas = []

    for nombre in nombres_texto:
        for value in texto_diccionario.values():
            if nombre in value and ((list(dic_preguntas_respuestas.values()).count(nombre)) < lim_preguntas) and value not in lista_frases_usadas:
                lista_frases_usadas.append(value)
                pregunta = value.replace(nombre, "__________")
                texto_frases_aux[pregunta] = value
                lista_preguntas_1.append(pregunta)
                dic_preguntas_respuestas[pregunta] = nombre
                break

    diccionario_Andres = {}
    # Eliminamos posibles repeticiones de preguntas.
    lista_preguntas = list(set(lista_preguntas_1))
    lista_opciones = []

    no_repetido = False

    m = 0

    # Si hay 2 nombres daremos esas dos opciones:
    contador_aux = 0

    if len(nombres_texto) == 2:
        for pregunta in lista_preguntas:
            while True:
                lista_opciones = [dic_preguntas_respuestas[pregunta],
                                  nombres_texto[random.randint(0, len(nombres_texto)-1)]]  # Creamos lista de opciones

        # Nos aseguramos de que en las opciones no hay nombres repetidos y de que las opciones no aparezcan ya en la pregunta:
                for opcion in lista_opciones:
                    for opcion1 in lista_opciones:
                        if opcion in opcion1 or opcion1 in opcion:
                            no_repetido = False
                        else:
                            no_repetido = True
                            break
                        if opcion.lower() in pregunta.lower() or opcion1.lower() in pregunta.lower():
                            if contador_aux < 5:
                                no_repetido = False
                                contador_aux += 1
                            else:
                                no_repetido = True
                        else:
                            no_repetido = False
                if len(set(lista_opciones)) == len(lista_opciones) and no_repetido:
                    break
            random.shuffle(lista_opciones)
            if 40 < len(pregunta) < 250 and len(pregunta.split(" ")) > 13 and "ej" not in pregunta.lower() and "ejemplo" not in pregunta.lower():
                m += 1
                diccionario_Andres[m] = [
                    dic_preguntas_respuestas[pregunta], pregunta, lista_opciones]
                try:
                    texto_frases_siguiente.remove(
                        texto_frases_aux[pregunta])
                except:
                    pass

    cont = 1
    contador_nombres = 0

    if len(nombres_texto) >= 3:
        for pregunta in lista_preguntas:
            if contador_nombres >= lim_preg_con_reserva:
                break
            while True:
                if dic_preguntas_respuestas[pregunta] in nombres_texto_masc and len(nombres_texto_masc) > 2:
                    lista_opciones = [dic_preguntas_respuestas[pregunta], nombres_texto_masc[random.randint(
                        0, len(nombres_texto_masc)-1)], nombres_texto_masc[random.randint(0, len(nombres_texto_masc)-1)]]

                elif dic_preguntas_respuestas[pregunta] in nombres_texto_fem and len(nombres_texto_fem) > 2:
                    lista_opciones = [dic_preguntas_respuestas[pregunta], nombres_texto_fem[random.randint(
                        0, len(nombres_texto_fem)-1)], nombres_texto_fem[random.randint(0, len(nombres_texto_fem)-1)]]

                else:
                    lista_opciones = [dic_preguntas_respuestas[pregunta], nombres_texto[random.randint(
                        0, len(nombres_texto)-1)], nombres_texto[random.randint(0, len(nombres_texto)-1)]]

                if lista_opciones[1] in pregunta or lista_opciones[2] in pregunta:
                    cont += 1
                    if cont >= 10:
                        pass
                        cont = 1
                    else:
                        continue
                cont = 1
                for opcion in lista_opciones:
                    for opcion1 in lista_opciones:
                        if opcion in opcion1 or opcion1 in opcion:
                            no_repetido = False
                        else:
                            no_repetido = True
                            break
                        if opcion.lower() in pregunta.lower() or opcion1.lower() in pregunta.lower():
                            if contador_aux < 10:
                                no_repetido = False
                                contador_aux += 1
                            else:
                                no_repetido = True
                        else:
                            no_repetido = False
                if len(set(lista_opciones)) == len(lista_opciones) and no_repetido:
                    break
            random.shuffle(lista_opciones)
            if 40 < len(pregunta) < 250 and len(pregunta.split(" ")) > 13 and "ej" not in pregunta.lower() and "ejemplo" not in pregunta.lower():
                m += 1
                diccionario_Andres[m] = [
                    dic_preguntas_respuestas[pregunta], pregunta, lista_opciones]
                contador_nombres += 1
                try:
                    texto_frases_siguiente.remove(
                        texto_frases_aux[pregunta])
                except:
                    pass

    listasv = diccionario_Andres.values()
    diccionario_bacanito = {}
    contv = 1
    verdaderito = "True"
    falsito = "False"
    for lista in listasv:
        if len(lista[1].split(" ")) < 25 and len(lista[1]) < 150 and contv <= floor(len(listasv)*0.4):
            randv = random.randint(0, 2)
            preguntav = lista[1].replace("__________", lista[2][randv])
            if lista[2][randv] == lista[0]:
                if idioma == "es":
                    respuestav = "Verdadero"
                    verdaderito = "Verdadero"
                    falsito = "Falso"
                elif idioma == "en":
                    respuestav = "True"
                    verdaderito = "True"
                    falsito = "False"
                elif idioma == "fr":
                    respuestav = "Vrai"
                    verdaderito = "Vrai"
                    falsito = "Faux"
                elif idioma == "it":
                    respuestav = "Vero"
                    verdaderito = "Vero"
                    falsito = "Falso"
                elif idioma == "pt":
                    respuestav = "Verdadeiro"
                    verdaderito = "Verdadeiro"
                    falsito = "Falso"
                else:
                    respuestav = "True"
                    verdaderito = "True"
                    falsito = "False"
            else:
                if idioma == "es":
                    respuestav = "Falso"
                    verdaderito = "Verdadero"
                    falsito = "Falso"
                elif idioma == "en":
                    respuestav = "False"
                    verdaderito = "True"
                    falsito = "False"
                elif idioma == "fr":
                    respuestav = "Faux"
                    verdaderito = "Vrai"
                    falsito = "Faux"
                elif idioma == "it":
                    respuestav = "Falso"
                    verdaderito = "Vero"
                    falsito = "Falso"
                elif idioma == "pt":
                    respuestav = "Falso"
                    verdaderito = "Verdadeiro"
                    falsito = "Falso"
                else:
                    respuestav = "False"
                    verdaderito = "True"
                    falsito = "False"
            diccionario_bacanito[contv] = [respuestav,
                                           preguntav, [verdaderito, falsito]]
        else:
            diccionario_bacanito[contv] = diccionario_Andres[contv]
        contv += 1

    # Vamos a añadir las preguntas de meses:

    meses_es = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    meses_en = ["January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"]
    meses_fr = ["janvier", "février", "mars", "avril", "mai", "juin",
                "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    meses_it = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
                "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
    meses_pt = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
                "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

    if idioma == "es":
        meses = meses_es
    elif idioma == "en":
        meses = meses_en
    elif idioma == "fr":
        meses = meses_fr
    elif idioma == "it":
        meses = meses_it
    elif idioma == "pt":
        meses = meses_pt
    else:
        meses = meses_es

    len_prev = len(diccionario_bacanito)

    contador_meses = 1
    for frase in texto_frases:
        for mes in meses:
            if mes in frase:
                if frase[frase.index(mes)-1] == " " and frase[frase.index(mes) + len(mes)] == " " and contador_meses <= 4 and 50 < len(frase) < 250 and len(frase.split(" ")) > 13:

                    lista_aux = [*meses]
                    lista_aux.remove(mes)

                    nueva_lista = random.sample(meses, 2)
                    nueva_lista.insert(random.randint(0, 2), mes)

                    diccionario_bacanito[contador_meses+len_prev] = [
                        mes, frase.replace(mes, '_________'), nueva_lista]

                    try:
                        texto_frases_siguiente.remove(frase)
                    except:
                        pass

                    contador_meses += 1

    # for [key, value] in diccionario_bacanito.items():
    #     print(f"{key}: {value}")
    #     print("\n")

    return [diccionario_bacanito, texto_frases_siguiente]

# La pregunta de lugares:


def preguntas_lugares(texto, idioma):
    # -*- coding: utf-8 -*-
    lugares = []  # Creamos lista inicial para los lugares
    lim_preguntas = 2  # Numero maximo de preguntas con la misma respuesta
    lugares = lugares_lista_url

    # Limpiamos un poco los lugares
    lista_valores_indeseados = [".", "?", "!", ")", "¿", "¡",
                                ":", "·", "<", ">", "-", "'", '"', '“', "”", "≪", "«", "»", "…", "\u00A4", "\u2022", "\u2023", "\u2218", "\u2219", "\u22C4", "\u22C5",
                                "\u22C6", "\u2311",  "\u2318", "\u2317",  "\u23F5", "\u25A0", "\u25A1",
                                "\u25A3", "\u25AA", "\u25AB", "\u25B2", "\u25B4", "\u25B8", "\u25BA", "\u25CB",
                                "\u25CF", "\u25E6", "\u25FB", "\u25FD", "\u25FE", "\u2662", "\u2666", "\u2756"]
    for lugar in lugares:
        if lugar[-1] in lista_valores_indeseados:
            lugar = lugar[: -1]

    # Como recibimos el texto for frases de la pregunta anterior hay que hacer un par de ajustes:
    # Abrimos el texto
    texto_diccionario = leer_archivo_dict_de_frases_str(
        " ".join(texto))

    texto_frases = texto

    texto_frases_siguiente = [frase for frase in texto_frases]
    texto_frases_aux = {}

    # Comprobamos que lugares de la lista estan en el texto
    lugares_texto = []
    for lugar in lugares:
        for value in texto_diccionario.values():
            if lugar.capitalize() in value and value[(value.index(lugar.capitalize())-1)] == " " and value[value.index(lugar.capitalize())+len(lugar.capitalize())] == " ":
                lugares_texto.append(lugar.capitalize())
    lugares_texto = list(set(lugares_texto))

    # Creamos las preguntas:
    diccionario_preguntas_respuestas = {}
    # La lista para hacer que no se haga más de una pregunta de la misma frase:
    lista_frases_usadas = []
    for lugar in lugares_texto:
        for value in texto_diccionario.values():
            if lugar in value and ((list(diccionario_preguntas_respuestas.values()).count(lugar)) < lim_preguntas and value not in lista_frases_usadas):
                lista_frases_usadas.append(value)
                pregunta = value.replace(lugar, "________")
                texto_frases_aux[pregunta] = value
                diccionario_preguntas_respuestas[pregunta] = lugar
                break

    # Si hay dos lugares haremos la pregunta con esas opciones

    m = 0
    diccionario_Andres = {}
    if len(lugares_texto) == 2:
        for pregunta in diccionario_preguntas_respuestas.keys():
            while True:
                lista_opciones = [diccionario_preguntas_respuestas[pregunta],
                                  lugares_texto[random.randint(0, len(lugares_texto)-1)]]
                for opcion in lista_opciones:
                    for opcion1 in lista_opciones:
                        if opcion in opcion1 or opcion1 in opcion:
                            Repetido = False
                        else:
                            Repetido = True
                            break
                if len(set(lista_opciones)) == len(lista_opciones) and Repetido:
                    break
            random.shuffle(lista_opciones)
            if 50 < len(pregunta) < 250 and len(pregunta.split(" ")) > 13:
                m += 1
                diccionario_Andres[m] = [
                    diccionario_preguntas_respuestas[pregunta], pregunta, lista_opciones]

                texto_frases_siguiente.remove(texto_frases_aux[pregunta])

    contador_lugares = 0
    # Si hay 3 damos 3 opciones:
    if len(lugares_texto) >= 3:
        for pregunta in diccionario_preguntas_respuestas.keys():
            if contador_lugares >= lim_preg_con_reserva-5:
                break
            while True:
                lista_opciones = [diccionario_preguntas_respuestas[pregunta], lugares_texto[random.randint(
                    0, len(lugares_texto)-1)], lugares_texto[random.randint(0, len(lugares_texto)-1)]]

                cont = 1
                # Comprobamos que las opciones no estén ya en las frases:
                if lista_opciones[1] in pregunta or lista_opciones[2] in pregunta:
                    cont += 1
                    if cont >= 10:
                        pass
                        cont = 1
                    else:
                        continue
                cont = 1
                # Comprobamos que no se repitan opciones:
                for opcion in lista_opciones:
                    for opcion1 in lista_opciones:
                        if opcion1 == opcion:
                            continue
                        if opcion in opcion1 or opcion1 in opcion:
                            Repetido = False
                        else:
                            Repetido = True
                            break
                if len(set(lista_opciones)) == len(lista_opciones) and Repetido:
                    break

            random.shuffle(lista_opciones)

            if 50 < len(pregunta) < 250 and len(pregunta.split(" ")) > 13:
                m += 1
                diccionario_Andres[m] = [
                    diccionario_preguntas_respuestas[pregunta], pregunta, lista_opciones]
                contador_lugares += 1
                texto_frases_siguiente.remove(texto_frases_aux[pregunta])

    listasv = diccionario_Andres.values()
    diccionario_bacanito = {}
    contv = 1
    # verdaderito = "True"
    # falsito = "False"
    for lista in listasv:
        if len(lista[1].split(" ")) < 25 and len(lista[1]) < 150 and contv <= floor(len(listasv)*0.4):
            randv = random.randint(0, 2)
            preguntav = lista[1].replace("________", lista[2][randv])
            if lista[2][randv] == lista[0]:
                if idioma == "es":
                    respuestav = "Verdadero"
                    verdaderito = "Verdadero"
                    falsito = "Falso"
                elif idioma == "en":
                    respuestav = "True"
                    verdaderito = "True"
                    falsito = "False"
                elif idioma == "fr":
                    respuestav = "Vrai"
                    verdaderito = "Vrai"
                    falsito = "Faux"
                elif idioma == "it":
                    respuestav = "Vero"
                    verdaderito = "Vero"
                    falsito = "Falso"
                elif idioma == "pt":
                    respuestav = "Verdadeiro"
                    verdaderito = "Verdadeiro"
                    falsito = "Falso"
                else:
                    respuestav = "True"
                    verdaderito = "True"
                    falsito = "False"
            else:
                if idioma == "es":
                    respuestav = "Falso"
                    verdaderito = "Verdadero"
                    falsito = "Falso"
                elif idioma == "en":
                    respuestav = "False"
                    verdaderito = "True"
                    falsito = "False"
                elif idioma == "fr":
                    respuestav = "Faux"
                    verdaderito = "Vrai"
                    falsito = "Faux"
                elif idioma == "it":
                    respuestav = "Falso"
                    verdaderito = "Vero"
                    falsito = "Falso"
                elif idioma == "pt":
                    respuestav = "Falso"
                    verdaderito = "Verdadeiro"
                    falsito = "Falso"
                else:
                    respuestav = "False"
                    verdaderito = "True"
                    falsito = "False"
            diccionario_bacanito[contv] = [respuestav,
                                           preguntav, [verdaderito, falsito]]
        else:
            diccionario_bacanito[contv] = diccionario_Andres[contv]
        contv += 1

    return [diccionario_bacanito, texto_frases_siguiente]


# La pregunta de fechas:

def preguntas_fechas(texto, idioma):

    # Primero leemos el texto por palabras y por frases:
    texto_palabras = leer_archivo_palabras_separadas(
        " ".join(texto))

    # Como recibimos el texto for frases de la pregunta anterior hay que hacer un par de ajustes:
    # Abrimos el texto

    texto_frases = texto

    texto_frases_siguiente = [frase for frase in texto_frases]

    numeros = []

    # Guardamos los números en una lista:
    for palabra in texto_palabras:
        try:
            numeros.append(
                int(palabra.strip('').replace(" ", "").replace("¿", "").replace("¡", "").replace("…", "").replace("_", "").replace("-", "").replace(")", "").replace(
                    "(", "").replace("...", "").replace("", "").replace("/", "").replace(".", "").replace(",", "").replace("≪", "").replace("«", "").replace("»", "").replace("'", "").replace('"', "").replace(":", "").replace(";", "").replace("?", "").replace("!", "").replace('“', "").replace("”", "")))
        except:
            pass
        # Ponemos esto para intentar solucionar lo de que coge un número entero como (1939-1950) y eso no se puede convertir a int:
        try:
            palabra_split = palabra.split('-')
            numeros.append(
                int(palabra_split[0].strip('').replace("¿", "").replace("¡", "").replace(" ", "").replace("…", "").replace("_", "").replace("-", "").replace(")", "").replace(
                    "(", "").replace("...", "").replace("", "").replace("/", "").replace(".", "").replace(",", "").replace("'", "").replace('"', "").replace(":", "").replace(";", "").replace("?", "").replace("!", "").replace('“', "").replace("”", "").replace("\u00A4", "").replace("\u2022", "").replace("\u2023", "").replace("\u2218", "").replace("\u2219", "").replace("\u22C4", "").replace("\u22C5", "").replace("\u22C6", "").replace("\u2311", "").replace("\u2318", "").replace("\u2317", "").replace("\u23F5", "").replace("\u25A0", "").replace("\u25A1", "").replace("\u25A3", "").replace("\u25AA", "").replace("\u25AB", "").replace("\u25B2", "").replace("\u25B4", "").replace("\u25B8", "").replace("\u25BA", "").replace("\u25CB", "").replace("\u25CF", "").replace("\u25E6", "").replace("\u25FB", "").replace("\u25FD", "").replace("\u25FE", "").replace("\u2662", "").replace("\u2666", "").replace("\u2756", "")))
            numeros.append(
                int(palabra_split[1].strip('').replace("¿", "").replace("¡", "").replace(" ", "").replace("…", "").replace("_", "").replace("-", "").replace(")", "").replace(
                    "(", "").replace("...", "").replace("", "").replace("/", "").replace("≪", "").replace("«", "").replace("»", "").replace(".", "").replace(",", "").replace("'", "").replace('"', "").replace(":", "").replace(";", "").replace("?", "").replace("!", "").replace('“', "").replace("”", "").replace("\u00A4", "").replace("\u2022", "").replace("\u2023", "").replace("\u2218", "").replace("\u2219", "").replace("\u22C4", "").replace("\u22C5", "").replace("\u22C6", "").replace("\u2311", "").replace("\u2318", "").replace("\u2317", "").replace("\u23F5", "").replace("\u25A0", "").replace("\u25A1", "").replace("\u25A3", "").replace("\u25AA", "").replace("\u25AB", "").replace("\u25B2", "").replace("\u25B4", "").replace("\u25B8", "").replace("\u25BA", "").replace("\u25CB", "").replace("\u25CF", "").replace("\u25E6", "").replace("\u25FB", "").replace("\u25FD", "").replace("\u25FE", "").replace("\u2662", "").replace("\u2666", "").replace("\u2756", "")))
        except:
            pass

    # Vamos a hacer ahora 2 listas con los números de 3 dígitos y 3 dígitos:
    numeros_3_dig = []
    for num3 in numeros:
        if num3 != 000 and num3 != 100 and len(str(num3)) == 3:
            numeros_3_dig.append(num3)
    numeros_3_dig = list(set(numeros_3_dig))

    numeros_4_dig = []
    for num4 in numeros:
        if num4 != 0000 and len(str(num4)) == 4:
            numeros_4_dig.append(num4)
    numeros_4_dig = list(set(numeros_4_dig))

    # Vamos a guardar los números que ya han salido en una lista para no repetirlos:
    lista_numeros = []
    lista_frases = []

    contador = 1
    contador_fechas = 0
    preguntas_fechas = {}
    for num in numeros:
        for frase in texto_frases:
            if contador_fechas >= lim_preg_con_reserva:
                break
            try:
                if str(num) in frase and 25 < len(frase) < 250 and num != 000 and len(str(num)) == 3 and frase not in lista_frases and texto_frases[texto_frases.index(frase)+1].split(" ")[0] != "000" and frase[frase.index(str(num))+len(str(num))] != "0" and frase[frase.index(str(num))+len(str(num))] != ".":
                    # Guardamos todos los números de esa frase en una lista para luego hacer que si hay otro número compararlo con el de la pregunta
                    numeros_temp = []
                    for num_aux in numeros_3_dig:
                        if str(num_aux) in frase:
                            numeros_temp.append(num_aux)

                    numeros_temp = list(set(numeros_temp))

                    # Ponemos un margen predefinido para el valor máximo de las fechas:
                    margen = 20

                    if len(numeros_temp) == 2:

                        numeros_temp.remove(num)
                        margen = abs(numeros_temp[0]-num)

                        # Vamos a evitar fallos de bucles inifinitos:
                        if margen == 0:
                            margen = 1

                        numero1 = 0
                        numero2 = 0

                        # Ahora distinguimos entre si va antes o después para las fechas:
                        if frase.index(str(numeros_temp[0])) < frase.index(str(num)):
                            while True:
                                numero1 = random.randint(
                                    num-margen, num+margen)
                                numero2 = random.randint(
                                    num-margen, num+margen)
                                if numero1 != numero2 and numero1 != num and numero2 != num:
                                    opciones = [str(num), str(
                                        numero1), str(numero2)]
                                    random.shuffle(opciones)
                                    break
                        if frase.index(str(numeros_temp[0])) > frase.index(str(num)):
                            while True:
                                numero1 = random.randint(
                                    num-margen, num+margen)
                                numero2 = random.randint(
                                    num-margen, num+margen)
                                if numero1 != numero2 and numero1 != num and numero2 != num:
                                    opciones = [str(num), str(
                                        numero1), str(numero2)]
                                    random.shuffle(opciones)
                                    break

                    # Si la longitud no es 2 ya no podemos hacer esto:
                    if len(numeros_temp) != 2:
                        numero1 = 0
                        numero2 = 0
                        while True:
                            numero1 = random.randint(num-20, num+20)
                            numero2 = random.randint(num-20, num+20)
                            if numero1 != numero2 and numero1 != num and numero2 != num:
                                opciones = [str(num), str(
                                    numero1), str(numero2)]
                                random.shuffle(opciones)
                                break

                    # De momento ponemos que no se añadan si hay más de 3 números en la misma frase ya que no funciona muy bien:
                    # Si la frase mide menos de 40 le añadimos la anterior frase:
                    if frase not in lista_frases and lista_numeros.count(str(num)) < 2 and len(numeros_temp) < 3 and str(num) in frase:
                        if 50 < len(frase) < 250 and len(frase.split(" ")) > 13:
                            preguntas_fechas[contador] = [
                                str(num), frase.replace(str(num), "_"*len(str(num))), opciones]
                            try:
                                texto_frases_siguiente.remove(frase)
                            except:
                                pass
                            lista_numeros.append(str(num))
                            contador += 1
                            lista_frases.append(frase)
                            contador_fechas += 1
                            break
            except:
                pass

            try:
                if str(num) in frase and 25 < len(frase) < 250 and len(str(num)) == 4 and num != 0000 and str(num)[0] == "1" and frase not in lista_frases and texto_frases[texto_frases.index(frase)+1].split(" ")[0] != "000" and frase[frase.index(str(num))+len(str(num))] != "0" and frase[frase.index(str(num))+len(str(num))] != ".":
                    # Guardamos todos los números de esa frase en una lista para luego hacer que si hay otro número compararlo con el de la pregunta
                    numeros_temp = []
                    for num_aux in numeros_4_dig:
                        if str(num_aux) in frase:
                            numeros_temp.append(num_aux)

                    numeros_temp = list(set(numeros_temp))
                    # print(frase)
                    # print(numeros_temp)

                    # Ponemos un margen predefinido para el valor máximo de las fechas:
                    margen = 20

                    if len(numeros_temp) == 2:

                        numeros_temp.remove(num)
                        margen = abs(numeros_temp[0]-num)

                        # Vamos a evitar fallos de bucles inifinitos:
                        if margen == 0:
                            margen = 1

                        numero1 = 0
                        numero2 = 0

                        # Ahora distinguimos entre si va antes o después para las fechas:
                        if frase.index(str(numeros_temp[0])) < frase.index(str(num)):

                            while True:
                                numero1 = random.randint(
                                    num-margen+1, num+margen*3)
                                numero2 = random.randint(
                                    num-margen+1, num+margen*3)
                                if numero1 != numero2 and numero1 != num and numero2 != num:
                                    opciones = [str(num), str(
                                        numero1), str(numero2)]
                                    random.shuffle(opciones)
                                    break
                        if frase.index(str(numeros_temp[0])) > frase.index(str(num)):
                            while True:
                                numero1 = random.randint(
                                    num-margen*3, num+margen-1)
                                numero2 = random.randint(
                                    num-margen*3, num+margen-1)
                                if numero1 != numero2 and numero1 != num and numero2 != num:
                                    opciones = [str(num), str(
                                        numero1), str(numero2)]

                                    random.shuffle(opciones)
                                    break

                    # Hay que volver a crear numeros temp ya que antes nos la hemos cargado:
                    numeros_temp = []
                    for num_aux in numeros_4_dig:
                        if str(num_aux) in frase:
                            numeros_temp.append(num_aux)

                    numeros_temp = list(set(numeros_temp))

                    # Si la longitud no es 2 ya no podemos hacer esto:
                    if len(numeros_temp) != 2 and len(numeros_temp) != 0:
                        numero1 = 0
                        numero2 = 0
                        while True:
                            numero1 = random.randint(num-20, num+20)
                            numero2 = random.randint(num-20, num+20)
                            if numero1 != numero2 and numero1 != num and numero2 != num:
                                opciones = [str(num), str(
                                    numero1), str(numero2)]

                                random.shuffle(opciones)
                                break

                    # Si la frase mide menos de 40 le añadimos la anterior frase:
                    if frase not in lista_frases and lista_numeros.count(str(num)) < 2 and len(numeros_temp) < 3 and str(num) in frase:
                        if 50 < len(frase) < 250 and len(frase.split(" ")) > 13:
                            preguntas_fechas[contador] = [
                                str(num), frase.replace(str(num), "_"*len(str(num))), opciones]
                            try:
                                texto_frases_siguiente.remove(frase)
                            except:
                                pass
                            lista_numeros.append(str(num))
                            contador += 1
                            lista_frases.append(frase)
                            contador_fechas += 1
                            break

                    # De momento ponemos que no se añadan si hay más de 3 números en la misma frase ya que no funciona muy bien
            except:
                pass

    listasv = preguntas_fechas.values()
    diccionario_bacanito = {}
    contv = 1
    verdaderito = "True"
    falsito = "False"
    for lista in listasv:
        if len(lista[1].split(" ")) < 25 and len(lista[1]) < 150 and contv <= floor(len(listasv)*0.4):
            randv = random.randint(0, 2)
            if ("____") in lista[1]:
                preguntav = lista[1].replace("____", lista[2][randv])
            else:
                preguntav = lista[1].replace("___", lista[2][randv])
            if lista[2][randv] == lista[0]:
                if idioma == "es":
                    respuestav = "Verdadero"
                    verdaderito = "Verdadero"
                    falsito = "Falso"
                elif idioma == "en":
                    respuestav = "True"
                    verdaderito = "True"
                    falsito = "False"
                elif idioma == "fr":
                    respuestav = "Vrai"
                    verdaderito = "Vrai"
                    falsito = "Faux"
                elif idioma == "it":
                    respuestav = "Vero"
                    verdaderito = "Vero"
                    falsito = "Falso"
                elif idioma == "pt":
                    respuestav = "Verdadeiro"
                    verdaderito = "Verdadeiro"
                    falsito = "Falso"
                else:
                    respuestav = "True"
                    verdaderito = "True"
                    falsito = "False"
            else:
                if idioma == "es":
                    respuestav = "Falso"
                    verdaderito = "Verdadero"
                    falsito = "Falso"
                elif idioma == "en":
                    respuestav = "False"
                    verdaderito = "True"
                    falsito = "False"
                elif idioma == "fr":
                    respuestav = "Faux"
                    verdaderito = "Vrai"
                    falsito = "Faux"
                elif idioma == "it":
                    respuestav = "Falso"
                    verdaderito = "Vero"
                    falsito = "Falso"
                elif idioma == "pt":
                    respuestav = "Falso"
                    verdaderito = "Verdadeiro"
                    falsito = "Falso"
                else:
                    respuestav = "False"
                    verdaderito = "True"
                    falsito = "False"
            diccionario_bacanito[contv] = [respuestav,
                                           preguntav, [verdaderito, falsito]]
        else:
            diccionario_bacanito[contv] = preguntas_fechas[contv]
        contv += 1

    return [diccionario_bacanito, texto_frases_siguiente]


# La pregunta de dos puntos:

def preguntas_dos_puntos(texto, lim_preg):

    stopwords = []
    verbos = []

    # Creamos la lista de stopwords:
    stopwords = [stopword.replace(" ", "").capitalize()
                 for stopword in stopwords_lista_url]

    for verbo in verbos_lista_url:
        stopwords.append(verbo.capitalize())

    for verbo in verbos_conjugados_lista_url:
        stopwords.append(verbo.capitalize())

    # Como recibimos el texto for frases de la pregunta anterior hay que hacer un par de ajustes:
    # Abrimos el texto

    texto_diccionario = leer_archivo_dict_de_frases_str(
        " ".join(texto))

    texto_frases = texto

    texto_frases_siguiente = [frase for frase in texto_frases]

    lista_frases = []
    for value in texto_diccionario.values():
        if ":" in value:
            lista_frases.append(str(value))

    dic_frases = {}
    for frase in lista_frases:
        lugar = frase.find(":")
        frase1 = frase[0:lugar+1]
        frase2 = frase[(lugar+1):len(frase)]
        if len(frase2.split(" ")) <= 40:
            dic_frases[frase2] = frase1
    preguntas = []
    respuestas = []
    diccionario_Andres = {}
    m = 0
    contador_dos_puntos = 0
    for frase2 in dic_frases.keys():

        if contador_dos_puntos >= lim_preg:
            break

        palabras = []
        palabras_bak = []

        palabras_1 = frase2.split(" ")
        for palabra in palabras_1:
            palabra = str(palabra).replace(
                " ", "").replace(".", "").replace(",", "")
            palabras.append(palabra)

        for palabra in palabras:

            palabra_aux = palabra.strip('').replace("…", "").replace(" ", "").replace("_", "").replace("-", "").replace(")", "").replace(
                "(", "").replace("", "").replace("¿", "").replace("¡", "").replace("...", "").replace("≪", "").replace("«", "").replace("»", "").replace("/", "").replace("«", "").replace("»", "").replace(".", "").replace(",", "").replace("'", "").replace('"', "").replace(":", "").replace(";", "").replace("?", "").replace("!", "").replace('“', "").replace("”", "").replace("\u00A4", "").replace("\u2022", "").replace("\u2023", "").replace("\u2218", "").replace("\u2219", "").replace("\u22C4", "").replace("\u22C5", "").replace("\u22C6", "").replace("\u2311", "").replace("\u2318", "").replace("\u2317", "").replace("\u23F5", "").replace("\u25A0", "").replace("\u25A1", "").replace("\u25A3", "").replace("\u25AA", "").replace("\u25AB", "").replace("\u25B2", "").replace("\u25B4", "").replace("\u25B8", "").replace("\u25BA", "").replace("\u25CB", "").replace("\u25CF", "").replace("\u25E6", "").replace("\u25FB", "").replace("\u25FD", "").replace("\u25FE", "").replace("\u2662", "").replace("\u2666", "").replace("\u2756", "")

            if palabra_aux.capitalize() in stopwords or palabra_aux.endswith('mente') or palabra_aux.capitalize() in verbos or palabra == "" or palabra == " " or palabra[0].isupper():
                continue

            es_numero = False
            try:
                int(palabra.strip('').replace("...", "").replace("…", "").replace(" ", "").replace("_", "").replace("-", "").replace(")", "").replace(
                    "(", "").replace("", "").replace("/", "").replace("¿", "").replace("¡", "").replace("≪", "").replace("«", "").replace("»", "").replace(".", "").replace(",", "").replace("'", "").replace('"', "").replace(":", "").replace(";", "").replace("?", "").replace("!", "").replace("\u00A4", "").replace("\u2022", "").replace("\u2023", "").replace("\u2218", "").replace("\u2219", "").replace("\u22C4", "").replace("\u22C5", "").replace("\u22C6", "").replace("\u2311", "").replace("\u2318", "").replace("\u2317", "").replace("\u23F5", "").replace("\u25A0", "").replace("\u25A1", "").replace("\u25A3", "").replace("\u25AA", "").replace("\u25AB", "").replace("\u25B2", "").replace("\u25B4", "").replace("\u25B8", "").replace("\u25BA", "").replace("\u25CB", "").replace("\u25CF", "").replace("\u25E6", "").replace("\u25FB", "").replace("\u25FD", "").replace("\u25FE", "").replace("\u2662", "").replace("\u2666", "").replace("\u2756", ""))
                es_numero = True
            except:
                pass

            try:
                palabra_split = palabra.split('-')
                int(palabra_split[0].strip('').replace(" ", "").replace("…", "").replace("_", "").replace("-", "").replace(")", "").replace(
                    "(", "").replace("", "").replace("¿", "").replace("¡", "").replace("...", "").replace("≪", "").replace("«", "").replace("»", "").replace(",", "≪").replace("/", "").replace(".", "").replace(",", "").replace("'", "").replace('"', "").replace(":", "").replace(";", "").replace("?", "").replace("!", "").replace("\u00A4", "").replace("\u2022", "").replace("\u2023", "").replace("\u2218", "").replace("\u2219", "").replace("\u22C4", "").replace("\u22C5", "").replace("\u22C6", "").replace("\u2311", "").replace("\u2318", "").replace("\u2317", "").replace("\u23F5", "").replace("\u25A0", "").replace("\u25A1", "").replace("\u25A3", "").replace("\u25AA", "").replace("\u25AB", "").replace("\u25B2", "").replace("\u25B4", "").replace("\u25B8", "").replace("\u25BA", "").replace("\u25CB", "").replace("\u25CF", "").replace("\u25E6", "").replace("\u25FB", "").replace("\u25FD", "").replace("\u25FE", "").replace("\u2662", "").replace("\u2666", "").replace("\u2756", ""))
                es_numero = True
            except:
                pass

            try:
                palabra_split = palabra.split('-')
                int(palabra_split[1].strip('').replace(" ", "").replace("…", "").replace("_", "").replace("-", "").replace(")", "").replace(
                    "(", "").replace("", "").replace("...", "").replace("¿", "").replace("¡", "").replace("≪", "").replace("«", "").replace("»", "").replace("/", "").replace(".", "").replace("«", "").replace("»", "").replace(",", "").replace("'", "").replace('"', "").replace(":", "").replace(";", "").replace("?", "").replace("!", "").replace("\u00A4", "").replace("\u2022", "").replace("\u2023", "").replace("\u2218", "").replace("\u2219", "").replace("\u22C4", "").replace("\u22C5", "").replace("\u22C6", "").replace("\u2311", "").replace("\u2318", "").replace("\u2317", "").replace("\u23F5", "").replace("\u25A0", "").replace("\u25A1", "").replace("\u25A3", "").replace("\u25AA", "").replace("\u25AB", "").replace("\u25B2", "").replace("\u25B4", "").replace("\u25B8", "").replace("\u25BA", "").replace("\u25CB", "").replace("\u25CF", "").replace("\u25E6", "").replace("\u25FB", "").replace("\u25FD", "").replace("\u25FE", "").replace("\u2662", "").replace("\u2666", "").replace("\u2756", ""))
                es_numero = True
            except:
                pass

            if es_numero:
                continue

            elif 4 < len(palabra) < 20:
                palabras_bak.append(palabra)

        if len(palabras_bak) > 1:
            palabra_quitar = palabras_bak[random.randint(
                0, len(palabras_bak)-1)]
            m += 1
        elif len(palabras_bak) > 0:
            palabra_quitar = palabras_bak[0]
            m += 1
        else:
            continue
        if 60 < len(dic_frases[frase2]+frase2) < 250 and len((dic_frases[frase2]+frase2).split(" ")) > 13:
            palabra_quitar_limpia = palabra_quitar.strip('').replace("…", "").replace(" ", "").replace("_", "").replace("-", "").replace(")", "").replace(
                "(", "").replace("", "").replace("¿", "").replace("¡", "").replace("...", "").replace("≪", "").replace("«", "").replace("»", "").replace("/", "").replace("«", "").replace("»", "").replace(".", "").replace(",", "").replace("'", "").replace('"', "").replace(":", "").replace(";", "").replace("?", "").replace("!", "").replace('“', "").replace("”", "").replace("\u00A4", "").replace("\u2022", "").replace("\u2023", "").replace("\u2218", "").replace("\u2219", "").replace("\u22C4", "").replace("\u22C5", "").replace("\u22C6", "").replace("\u2311", "").replace("\u2318", "").replace("\u2317", "").replace("\u23F5", "").replace("\u25A0", "").replace("\u25A1", "").replace("\u25A3", "").replace("\u25AA", "").replace("\u25AB", "").replace("\u25B2", "").replace("\u25B4", "").replace("\u25B8", "").replace("\u25BA", "").replace("\u25CB", "").replace("\u25CF", "").replace("\u25E6", "").replace("\u25FB", "").replace("\u25FD", "").replace("\u25FE", "").replace("\u2662", "").replace("\u2666", "").replace("\u2756", "")

            if palabra_quitar_limpia in frase2:
                preguntas.append(frase2.replace(
                    palabra_quitar_limpia, "_"*len(palabra_quitar_limpia)))
                respuestas.append(palabra_quitar_limpia)
                diccionario_Andres[m] = [palabra_quitar_limpia,
                                         dic_frases[frase2]+frase2.replace(palabra_quitar_limpia, "_"*len(palabra_quitar_limpia))]
                try:
                    texto_frases_siguiente.remove(dic_frases[frase2]+frase2)
                except:
                    pass
                contador_dos_puntos += 1

    # Arreglamos el diccionario:
    dict_bueno = {}
    contador = 1
    for key in diccionario_Andres.keys():
        dict_bueno[contador] = diccionario_Andres[key]
        contador += 1

    return [dict_bueno, texto_frases_siguiente]


# La pregunta de mayúsculas:

def preguntas_mayusculas(texto, lim_preg):

    # En la última pregunta no hace falta ya pasar el texto sin las frases que has usado

    # Hacemos una lista con nombres propios,stopwords y otra con los lugares para no incluirlos en este tipo de preguntas:
    nombres = []
    apellidos = []
    lugares = []
    stopwords = []

    # Leemos el archivo txt de los nombres
    nombres = [nombre.replace(" ", "")
               for nombre in nombres_propios_lista_url]

    apellidos = [apellido.replace(" ", "") for apellido in apellidos_lista_url]

    lugares = [lugares.replace(" ", "") for lugares in lugares_lista_url]

    # Leemos el archivo de stopwords:
    stopwords = [stopword.capitalize()
                 for stopword in stopwords_lista_url]

    # Leemos el texto:
    texto_diccionario = leer_archivo_dict_de_frases_separadas(
        " ".join(texto))

    # Creamos el dict de preguntas:
    dict_frases_palabra = {}

    lista_valores_indeseados = [".", "?", "!", "¿", "¡",
                                ")", ":", "·", "<", ">", "-", "'", '"', '', '“', "”", "...", "«", "»", "…",
                                "\u00A4", "\u2022", "\u2023", "\u2218", "\u2219", "\u22C4", "\u22C5",
                                "\u22C6", "\u2311",  "\u2318", "\u2317",  "\u23F5", "\u25A0", "\u25A1",
                                "\u25A3", "\u25AA", "\u25AB", "\u25B2", "\u25B4", "\u25B8", "\u25BA", "\u25CB",
                                "\u25CF", "\u25E6", "\u25FB", "\u25FD", "\u25FE", "\u2662", "\u2666", "\u2756"]

    lista_frases_ya_salidas = []
    contador_mayusculas = 0
    # Añadimos toda la lista de preguntas:
    dict_palabras_ya_salidas = {}
    for key in texto_diccionario.keys():
        if contador_mayusculas >= lim_preg:
            break

        lista_aux = []
        dict_frases_palabra[key] = [[], " ".join(texto_diccionario[key])]
        for palabra in texto_diccionario[key]:
            palabra2 = palabra.strip('').replace(" ", "").replace("¿", "").replace("¡", "").replace("_", "").replace("-", "").replace("…", "").replace("≪", "").replace("«", "").replace("»", "").replace(")", "").replace(
                "(", "").replace("...", "").replace("", "").replace("/", "").replace("≪", "").replace("«", "").replace("»", "").replace(".", "").replace(",", "").replace("'", "").replace('"', "").replace(":", "").replace(";", "").replace("?", "").replace("!", "").replace('“', "").replace("”", "").replace("\u00A4", "").replace("\u2022", "").replace("\u2023", "").replace("\u2218", "").replace("\u2219", "").replace("\u22C4", "").replace("\u22C5", "").replace("\u22C6", "").replace("\u2311", "").replace("\u2318", "").replace("\u2317", "").replace("\u23F5", "").replace("\u25A0", "").replace("\u25A1", "").replace("\u25A3", "").replace("\u25AA", "").replace("\u25AB", "").replace("\u25B2", "").replace("\u25B4", "").replace("\u25B8", "").replace("\u25BA", "").replace("\u25CB", "").replace("\u25CF", "").replace("\u25E6", "").replace("\u25FB", "").replace("\u25FD", "").replace("\u25FE", "").replace("\u2662", "").replace("\u2666", "").replace("\u2756", "")
            try:
                # Hacemos todas las comprobaciones:
                if 60 < len(" ".join(texto_diccionario[key])) < 250 and len((" ".join(texto_diccionario[key])).split(" ")) > 13 and palabra2.lower() not in ["bachillerato", "ejemplo", "ejemplos", "además", "ej", "ejs"] and palabra[0].isupper() and not palabra[1].isupper() and palabra2.capitalize() not in nombres and palabra2.capitalize() not in lugares and palabra2.capitalize() not in apellidos and palabra2.capitalize() not in stopwords and not palabra2.lower().endswith('mente') and texto_diccionario[key].index(palabra) != 0 and texto_diccionario[key].index(palabra) != 1 and texto_diccionario[key][texto_diccionario[key].index(palabra)-1][-1] not in lista_valores_indeseados and texto_diccionario[key] not in lista_frases_ya_salidas and 4 < len(palabra2) < 20:
                    # Si no está ya la entrada la creamos
                    if palabra2.lower() not in list(dict_palabras_ya_salidas.keys()):
                        dict_palabras_ya_salidas[palabra2.lower()] = 0
                    else:
                        dict_palabras_ya_salidas[palabra2.lower()] += 1

                    # Solo ponemos otra palabra si ha salido menos de 3 veces ya:
                    if dict_palabras_ya_salidas[palabra2.lower()] < 2:
                        lista_aux.append(palabra2)
                        lista_frases_ya_salidas.append(texto_diccionario[key])
            except:
                pass

        try:
            pregunta_palabra = random.choice(lista_aux).strip('').replace("¿", "").replace("¡", "").replace(" ", "").replace("_", "").replace("…", "").replace("-", "").replace(")", "").replace(
                "(", "").replace("", "").replace("...", "").replace("/", "").replace("≪", "").replace("«", "").replace("»", "").replace(".", "").replace(",", "").replace("'", "").replace('"', "").replace(":", "").replace(";", "").replace("?", "").replace("!", "").replace('“', "").replace("”", "").replace("\u00A4", "").replace("\u2022", "").replace("\u2023", "").replace("\u2218", "").replace("\u2219", "").replace("\u22C4", "").replace("\u22C5", "").replace("\u22C6", "").replace("\u2311", "").replace("\u2318", "").replace("\u2317", "").replace("\u23F5", "").replace("\u25A0", "").replace("\u25A1", "").replace("\u25A3", "").replace("\u25AA", "").replace("\u25AB", "").replace("\u25B2", "").replace("\u25B4", "").replace("\u25B8", "").replace("\u25BA", "").replace("\u25CB", "").replace("\u25CF", "").replace("\u25E6", "").replace("\u25FB", "").replace("\u25FD", "").replace("\u25FE", "").replace("\u2662", "").replace("\u2666", "").replace("\u2756", "")

            if pregunta_palabra in " ".join(texto_diccionario[key]):
                dict_frases_palabra[key] = [pregunta_palabra, " ".join(texto_diccionario[key]).replace(
                    pregunta_palabra, "_"*len(pregunta_palabra)).replace(pregunta_palabra.lower(), "_"*len(pregunta_palabra))]
                contador_mayusculas += 1
        except:
            pass

    # Vamos a guardar las únicas frases que tienen contenido:
    preg_mayus_buenas = {}
    contador = 1
    for key in dict_frases_palabra:
        if dict_frases_palabra[key][0] != []:
            preg_mayus_buenas[contador] = dict_frases_palabra[key]
            contador += 1

    return preg_mayus_buenas


#
#
#
#
#
#
#
#                                                            API:


def hacer_preguntas(storageId, pags, eliminarPaginas, pdf_url,):
    contador_total = 0

    args_dict = {}
    args_dict['storageId'] = storageId
    args_dict['pags'] = pags
    eliminarPaginas = eliminarPaginas
    pdf_url = pdf_url  # El link del pdf para extraerle el texto:

    # Vamos a crear la referencia al storage:
    config = {
        "apiKey": "",
        "authDomain": "",
        "databaseURL": "",
        "projectId": "",
        "storageBucket": "",
        "appId": "",
        "serviceAccount": "serviceAccountCredentials.json"
    }

    # Iniciamos nuestra conexión con firebase:
    firebase = pyrebase.initialize_app(config)

    # Creamos nuestra referencia al storage:
    storage = firebase.storage()

    # El path del archivo que usar:
    pdf_path = storageId

    # Empezamos las funciones:

    startTime0 = time.time()

    # Las páginas que borrar:
    if args_dict['pags'] != '':
        pag_list = args_dict['pags'].split(",")
        for pag in pag_list:
            pag_list[pag_list.index(pag)] = int(pag)
    else:
        pag_list = []
    # Ponemos bien la condición:
    if eliminarPaginas == "true":
        borrarPags = True
    # Si no, es decir, si hay que escoger las páginas:
    if eliminarPaginas == "false":
        borrarPags = False

    # Vamos a leer el texto haciendo una get request al Java y a limpiarlo con el beautifulSoup:
    # len_pagis = 1
    try:
        # El nombre del archivo de los credenciales:
        sa_filename = 'serviceAccountCredentials.json'

        # El lugar de la función de cloud functions:
        cloud_functions_url = "https://europe-west2-fastest-e5579.cloudfunctions.net/pruebaInternacionalizar"

        # Esto la verdad que no sé lo que significa pero también es el lugar de la función en cloud functions:
        aud = "https://europe-west2-fastest-e5579.cloudfunctions.net/pruebaInternacionalizar"

        # La función para conseguir el texto:
        def get_text_cloud_function(url, id_token):
            headers = {'Authorization': 'Bearer ' + id_token}

            params = {"name": pdf_url}
            r = requests.get(url, headers=headers, params=params)

            if r.status_code != 200:
                print('Calling endpoint failed')
                print('HTTP Status Code:', r.status_code)
                print(r.content)
                return None

            return r.content.decode('utf-8')

        # Los credenciales:
        credentials = IDTokenCredentials.from_service_account_file(
            sa_filename,
            target_audience=aud)

        request = google.auth.transport.requests.Request()
        credentials.refresh(request)
        texto_request_prev = get_text_cloud_function(
            cloud_functions_url, credentials.token)

        lista_doble = texto_request_prev.split("loschavalesbakanos23")

        texto_request = lista_doble[0]

        try:
            idioma = lista_doble[1]
        except:
            idioma = "es"

        if idioma != "es" and idioma != "en" and idioma != "it" and idioma != "fr" and idioma != "pt":
            idioma = "es"

        print("El idioma es: "+idioma)

        # Convertimos el texto xml en texto limpio y separamos el pdf con las páginas pasadas:
        texto_y_pags = archivo_a_texto(
            texto_request, lista=pag_list, borrar=borrarPags)

        # Esto de momento no lo ponemos ya que no nos sirve de nada si no hay una función para leer los de una página:
        # if pdf_url.endswith('pdf'):
        #     len_pagis = texto_y_pags[1]

        # Si no es pdf no le podemos separar las páginas
        texto_leido = texto_y_pags[0]

        with open("texto.txt", "w", encoding="utf-8") as archivo:
            archivo.write(texto_leido)

        texto_frases = leer_archivo_lista_de_strings(
            texto_leido)

        random.shuffle(texto_frases)

        texto_leido = " ".join(texto_frases)

        texto_lineas = texto_y_pags[0]

        print(
            f"Texto léido y páginas separadas. Ha tardado {time.time()-startTime0} segundos")
    except Exception as error:
        print(error)

    global verbos_lista_url
    global verbos_conjugados_lista_url
    global apellidos_lista_url
    global nombres_propios_lista_url
    global lugares_lista_url
    global stopwords_lista_url
    # Vamos a poner el idioma:
    if idioma == "es":
        # Español:
        url_verbos_esp = "https://firebasestorage.googleapis.com/v0/b/fastest-e5579.appspot.com/o/Archivos%20para%20usar%2Flista_verbos.txt?alt=media&token=0bd0cf43-d544-4adc-a4dc-a2237337601d"
        url_verbos_conjugados_esp = "https://firebasestorage.googleapis.com/v0/b/fastest-e5579.appspot.com/o/Archivos%20para%20usar%2Flista_verbos_conjugados.txt?alt=media&token=a95c4ed0-06ab-475c-837d-73639e2158c7"
        url_apellidos_esp = "https://firebasestorage.googleapis.com/v0/b/fastest-e5579.appspot.com/o/Archivos%20para%20usar%2Flista_apellidos.txt?alt=media&token=c6562bca-4555-4fb7-906f-9d7f0e3f61e4"
        url_nombres_esp = "https://firebasestorage.googleapis.com/v0/b/fastest-e5579.appspot.com/o/Archivos%20para%20usar%2Fnombres_propios_espa%C3%B1ol_actualizada.txt?alt=media&token=c7b8cf73-e028-448a-9739-6c8f629e388c"
        url_lugares_esp = "https://firebasestorage.googleapis.com/v0/b/fastest-e5579.appspot.com/o/Archivos%20para%20usar%2Flugares_espa%C3%B1ol.txt?alt=media&token=e4f6104b-2cb5-4778-9666-2eb49a0a460c"

        verbos_lista_r_esp = requests.get(url_verbos_esp)
        verbos_conjugados_lista_r_esp = requests.get(url_verbos_conjugados_esp)
        apellidos_lista_r_esp = requests.get(url_apellidos_esp)
        nombres_propios_lista_r_esp = requests.get(url_nombres_esp)
        lugares_lista_r_esp = requests.get(url_lugares_esp)

        verbos_lista_r_esp.encoding = "utf-8"
        verbos_conjugados_lista_r_esp.encoding = "utf-8"
        apellidos_lista_r_esp.encoding = "utf-8"
        nombres_propios_lista_r_esp.encoding = "utf-8"
        lugares_lista_r_esp.encoding = "utf-8"

        verbos_lista_url = verbos_lista_r_esp.text.replace(
            "\r", "").split("\n")
        verbos_conjugados_lista_url = verbos_conjugados_lista_r_esp.text.replace(
            "\r", "").split("\n")
        apellidos_lista_url = apellidos_lista_r_esp.text.replace(
            "\r", "").split("\n")
        nombres_propios_lista_url = nombres_propios_lista_r_esp.text.replace(
            "\r", "").split("\n")
        lugares_lista_url = lugares_lista_r_esp.text.replace(
            "\r", "").split("\n")
        stopwords_lista_url = ["a", "actualmente", "acuerdo", "adelante", "ademas", "además", "adrede", "afirmó", "agregó", "ahi", "ahora", "ahí", "al", "algo", "alguna", "algunas", "alguno", "algunos", "algún", "alli", "allí", "alrededor", "ambos", "ampleamos", "antano", "antaño", "ante", "anterior", "antes", "apenas", "aproximadamente", "aquel", "aquella", "aquellas", "aquello", "aquellos", "aqui", "aquél", "aquélla", "aquéllas", "aquéllos", "aquí", "arriba", "arribaabajo", "aseguró", "asi", "así", "atras", "aun", "aunque", "ayer", "añadió", "aún", "b", "bajo", "bastante", "bien", "breve", "buen", "buena", "buenas", "bueno", "buenos", "c", "cada", "casi", "cerca", "cierta", "ciertas", "cierto", "ciertos", "cinco", "claro", "comentó", "como", "con", "conmigo", "conocer", "conseguimos", "conseguir", "considera", "consideró", "consigo", "consigue", "consiguen", "consigues", "contigo", "contra", "cosas", "creo", "cual", "cuales", "cualquier", "cuando", "cuanta", "cuantas", "cuanto", "cuantos", "cuatro", "cuenta", "cuál", "cuáles", "cuándo", "cuánta", "cuántas", "cuánto", "cuántos", "cómo", "d", "da", "dado", "dan", "dar", "de", "debajo", "debe", "deben", "debido", "decir", "dejó", "del", "delante", "demasiado", "demás", "dentro", "deprisa", "desde", "despacio", "despues", "después", "detras", "detrás", "dia", "dias", "dice", "dicen", "dicho", "dieron", "diferente", "diferentes", "dijeron", "dijo", "dio", "donde", "dos", "durante", "día", "días", "dónde", "e", "ejemplo", "el", "ella", "ellas", "ello", "ellos", "embargo", "empleais", "emplean", "emplear", "empleas", "empleo", "en", "encima", "encuentra", "enfrente", "enseguida", "entonces", "entre", "era", "erais", "eramos", "eran", "eras", "eres", "es", "esa", "esas", "ese", "eso", "esos", "esta", "estaba", "estabais", "estaban", "estabas", "estad", "estada", "estadas", "estado", "estados", "estais", "estamos", "estan", "estando", "estar", "estaremos", "estará", "estarán", "estarás", "estaré", "estaréis", "estaría", "estaríais", "estaríamos", "estarían", "estarías", "estas", "este", "estemos", "esto", "estos", "estoy", "estuve", "estuviera", "estuvierais", "estuvieran", "estuvieras", "estuvieron", "estuviese", "estuvieseis", "estuviesen", "estuvieses", "estuvimos", "estuviste", "estuvisteis", "estuviéramos", "estuviésemos", "estuvo", "está", "estábamos", "estáis", "están", "estás", "esté", "estéis", "estén", "estés", "ex", "excepto", "existe", "existen", "explicó", "expresó", "f", "fin", "final", "fue", "fuera", "fuerais", "fueran", "fueras", "fueron", "fuese", "fueseis", "fuesen", "fueses", "fui", "fuimos", "fuiste", "fuisteis", "fuéramos", "fuésemos", "g", "general", "gran", "grandes", "gueno", "h", "ha", "haber", "habia", "habida", "habidas", "habido", "habidos", "habiendo", "habla", "hablan", "habremos", "habrá", "habrán", "habrás", "habré", "habréis", "habría", "habríais", "habríamos", "habrían", "habrías", "habéis", "había", "habíais", "habíamos", "habían", "habías", "hace", "haceis", "hacemos", "hacen", "hacer", "hacerlo", "haces", "hacia", "haciendo", "hago", "han", "has", "hasta", "hay", "haya", "hayamos", "hayan", "hayas", "hayáis", "he", "hecho", "hemos", "hicieron", "hizo", "horas", "hoy", "hube", "hubiera", "hubierais", "hubieran", "hubieras", "hubieron", "hubiese", "hubieseis", "hubiesen", "hubieses", "hubimos", "hubiste", "hubisteis", "hubiéramos", "hubiésemos", "hubo", "igual", "incluso", "indicó", "informo", "informó", "intenta", "intentais",
                               "intentamos", "intentan", "intentar", "intentas", "intento", "ir", "j", "junto", "k", "l", "la", "lado", "largo", "las", "le", "lejos", "les", "llegó", "lleva", "llevar", "lo", "los", "luego", "lugar", "m", "mal", "manera", "manifestó", "mas", "mayor", "me", "mediante", "medio", "mejor", "mencionó", "menos", "menudo", "mi", "mia", "mias", "mientras", "mio", "mios", "mis", "misma", "mismas", "mismo", "mismos", "modo", "momento", "mucha", "muchas", "mucho", "muchos", "muy", "más", "mí", "mía", "mías", "mío", "míos", "n", "nada", "nadie", "ni", "ninguna", "ningunas", "ninguno", "ningunos", "ningún", "no", "nos", "nosotras", "nosotros", "nuestra", "nuestras", "nuestro", "nuestros", "nueva", "nuevas", "nuevo", "nuevos", "nunca", "o", "ocho", "os", "otra", "otras", "otro", "otros", "p", "pais", "para", "parece", "parte", "partir", "pasada", "pasado", "paìs", "peor", "pero", "pesar", "poca", "pocas", "poco", "pocos", "podeis", "podemos", "poder", "podria", "podriais", "podriamos", "podrian", "podrias", "podrá", "podrán", "podría", "podrían", "poner", "por", "por qué", "porque", "posible", "primer", "primera", "primero", "primeros", "principalmente", "pronto", "propia", "propias", "propio", "propios", "proximo", "próximo", "próximos", "pudo", "pueda", "puede", "pueden", "puedo", "pues", "q", "qeu", "que", "quedó", "queremos", "quien", "quienes", "quiere", "quiza", "quizas", "quizá", "quizás", "quién", "quiénes", "qué", "r", "raras", "realizado", "realizar", "realizó", "repente", "respecto", "s", "sabe", "sabeis", "sabemos", "saben", "saber", "sabes", "sal", "salvo", "se", "sea", "seamos", "sean", "seas", "segun", "segunda", "segundo", "según", "seis", "ser", "sera", "seremos", "será", "serán", "serás", "seré", "seréis", "sería", "seríais", "seríamos", "serían", "serías", "seáis", "señaló", "si", "sido", "siempre", "siendo", "siete", "sigue", "siguiente", "sin", "sino", "sobre", "sois", "sola", "solamente", "solas", "solo", "solos", "somos", "son", "soy", "soyos", "su", "supuesto", "sus", "suya", "suyas", "suyo", "suyos", "sé", "sí", "sólo", "t", "tal", "tambien", "también", "tampoco", "tan", "tanto", "tarde", "te", "temprano", "tendremos", "tendrá", "tendrán", "tendrás", "tendré", "tendréis", "tendría", "tendríais", "tendríamos", "tendrían", "tendrías", "tened", "teneis", "tenemos", "tener", "tenga", "tengamos", "tengan", "tengas", "tengo", "tengáis", "tenida", "tenidas", "tenido", "tenidos", "teniendo", "tenéis", "tenía", "teníais", "teníamos", "tenían", "tenías", "tercera", "ti", "tiempo", "tiene", "tienen", "tienes", "toda", "todas", "todavia", "todavía", "todo", "todos", "total", "trabaja", "trabajais", "trabajamos", "trabajan", "trabajar", "trabajas", "trabajo", "tras", "trata", "través", "tres", "tu", "tus", "tuve", "tuviera", "tuvierais", "tuvieran", "tuvieras", "tuvieron", "tuviese", "tuvieseis", "tuviesen", "tuvieses", "tuvimos", "tuviste", "tuvisteis", "tuviéramos", "tuviésemos", "tuvo", "tuya", "tuyas", "tuyo", "tuyos", "tú", "u", "ultimo", "un", "una", "unas", "uno", "unos", "usa", "usais", "usamos", "usan", "usar", "usas", "uso", "usted", "ustedes", "va", "vais", "valor", "vamos", "van", "varias", "varios", "vaya", "veces", "ver", "verdad", "verdadera", "verdadero", "vez", "vosotras", "vosotros", "voy", "vuestra", "vuestras", "vuestro", "vuestros", "w", "y", "ya", "yo", "z", "él", "éramos", "ésa", "ésas", "ése", "ésos", "ésta", "éstas", "éste", "éstos", "última", "últimas", "último", "últimos"]

    elif idioma == "en":
        # Inglés:
        url_stopwords_en = "https://firebasestorage.googleapis.com/v0/b/fastest-e5579.appspot.com/o/Archivos%20para%20usar%2FIngl%C3%A9s%2Fenglish.txt?alt=media&token=2a639eb3-5307-48e3-a2d2-7994da38c8e9"
        url_nombres_en = "https://firebasestorage.googleapis.com/v0/b/fastest-e5579.appspot.com/o/Archivos%20para%20usar%2FIngl%C3%A9s%2Fnombres_ingles.txt?alt=media&token=823b277a-f35f-4b50-afa4-b576c8117180"
        url_lugares_en = "https://firebasestorage.googleapis.com/v0/b/fastest-e5579.appspot.com/o/Archivos%20para%20usar%2FIngl%C3%A9s%2Fenglish_places.txt?alt=media&token=e7010203-92e1-4044-869a-abd737c494d5"
        url_verbos_en = "https://firebasestorage.googleapis.com/v0/b/fastest-e5579.appspot.com/o/Archivos%20para%20usar%2FIngl%C3%A9s%2Fverbos_ingles.txt?alt=media&token=5e3d45d3-0dab-4227-b244-cddefcd02489"

        stopwords_lista_r_en = requests.get(url_stopwords_en)
        nombres_propios_lista_r_en = requests.get(url_nombres_en)
        lugares_lista_r_en = requests.get(url_lugares_en)
        verbos_lista_r_en = requests.get(url_verbos_en)

        stopwords_lista_r_en.encoding = "utf-8"
        nombres_propios_lista_r_en.encoding = "utf-8"
        lugares_lista_r_en.encoding = "utf-8"
        verbos_lista_r_en.encoding = "utf-8"

        stopwords_lista_url = stopwords_lista_r_en.text.replace(
            "\r", "").split("\n")
        verbos_lista_url = verbos_lista_r_en.text.replace(
            "\r", "").split("\n")
        verbos_conjugados_lista_url = verbos_lista_r_en.text.replace(
            "\r", "").split("\n")
        apellidos_lista_url = []
        nombres_propios_lista_url = nombres_propios_lista_r_en.text.replace(
            "\r", "").split("\n")
        lugares_lista_url = lugares_lista_r_en.text.replace(
            "\r", "").split("\n")

    elif idioma == "fr":

        # Francés:
        url_stopwords_fr = "https://firebasestorage.googleapis.com/v0/b/fastest-e5579.appspot.com/o/Archivos%20para%20usar%2FFranc%C3%A9s%2Ffrances.txt?alt=media&token=87f4aebd-690f-4fa9-a864-6f3fb7afa0a9"
        url_nombres_fr = "https://firebasestorage.googleapis.com/v0/b/fastest-e5579.appspot.com/o/Archivos%20para%20usar%2FFranc%C3%A9s%2Fnombres_frances.txt?alt=media&token=85614312-8e88-4cc5-b072-77f64b90e3fa"
        url_lugares_fr = "https://firebasestorage.googleapis.com/v0/b/fastest-e5579.appspot.com/o/Archivos%20para%20usar%2FFranc%C3%A9s%2Flieus_fran%C3%A7ais_defi.txt?alt=media&token=b6316688-b352-4566-b5ce-a2a1d22567a3"
        url_verbos_fr = "https://firebasestorage.googleapis.com/v0/b/fastest-e5579.appspot.com/o/Archivos%20para%20usar%2FFranc%C3%A9s%2Fverbos_frances.txt?alt=media&token=dea2e1d0-b41a-435f-a4dd-13915f451d30"

        stopwords_lista_r_fr = requests.get(url_stopwords_fr)
        nombres_propios_lista_r_fr = requests.get(url_nombres_fr)
        lugares_lista_r_fr = requests.get(url_lugares_fr)
        verbos_lista_r_fr = requests.get(url_verbos_fr)

        stopwords_lista_r_fr.encoding = "utf-8"
        nombres_propios_lista_r_fr.encoding = "utf-8"
        lugares_lista_r_fr.encoding = "utf-8"
        verbos_lista_r_fr.encoding = "utf-8"

        stopwords_lista_url = stopwords_lista_r_fr.text.replace(
            "\r", "").split("\n")
        verbos_lista_url = verbos_lista_r_fr.text.replace(
            "\r", "").split("\n")
        verbos_conjugados_lista_url = verbos_lista_r_fr.text.replace(
            "\r", "").split("\n")
        apellidos_lista_url = []
        nombres_propios_lista_url = nombres_propios_lista_r_fr.text.replace(
            "\r", "").split("\n")
        lugares_lista_url = lugares_lista_r_fr.text.replace(
            "\r", "").split("\n")

    elif idioma == "it":
        # Italiano
        url_stopwords_it = "https://firebasestorage.googleapis.com/v0/b/fastest-e5579.appspot.com/o/Archivos%20para%20usar%2FItaliano%2Fitaliano.txt?alt=media&token=a9539f49-963d-4b15-b2d3-e5a8843d4292"
        url_nombres_it = "https://firebasestorage.googleapis.com/v0/b/fastest-e5579.appspot.com/o/Archivos%20para%20usar%2FItaliano%2Fnombres_italiano.txt?alt=media&token=c2a7eb3b-cc45-4dfa-98b2-cea1ee9a2b4e"
        url_lugares_it = "https://firebasestorage.googleapis.com/v0/b/fastest-e5579.appspot.com/o/Archivos%20para%20usar%2FItaliano%2Flugares_italiano_defi.txt?alt=media&token=09ca5d55-9279-4eae-8865-92a87bb3ccd6"
        url_verbos_it = "https://firebasestorage.googleapis.com/v0/b/fastest-e5579.appspot.com/o/Archivos%20para%20usar%2FItaliano%2Fverbos_italiano.txt?alt=media&token=9549da86-645c-4fe9-8113-4a0f3356eb10"

        stopwords_lista_r_it = requests.get(url_stopwords_it)
        nombres_propios_lista_r_it = requests.get(url_nombres_it)
        lugares_lista_r_it = requests.get(url_lugares_it)
        verbos_lista_r_it = requests.get(url_verbos_it)

        stopwords_lista_r_it.encoding = "utf-8"
        nombres_propios_lista_r_it.encoding = "utf-8"
        lugares_lista_r_it.encoding = "utf-8"
        verbos_lista_r_it.encoding = "utf-8"

        stopwords_lista_url = stopwords_lista_r_it.text.replace(
            "\r", "").split("\n")
        verbos_lista_url = verbos_lista_r_it.text.replace(
            "\r", "").split("\n")
        verbos_conjugados_lista_url = verbos_lista_r_it.text.replace(
            "\r", "").split("\n")
        apellidos_lista_url = []
        nombres_propios_lista_url = nombres_propios_lista_r_it.text.replace(
            "\r", "").split("\n")
        lugares_lista_url = lugares_lista_r_it.text.replace(
            "\r", "").split("\n")

    elif idioma == "pt":
        # Portugués:
        url_stopwords_pt = "https://firebasestorage.googleapis.com/v0/b/fastest-e5579.appspot.com/o/Archivos%20para%20usar%2FPortugu%C3%A9s%2Fportugues.txt?alt=media&token=903cd07d-2030-46a4-9064-32890a52f2a3"
        url_nombres_pt = "https://firebasestorage.googleapis.com/v0/b/fastest-e5579.appspot.com/o/Archivos%20para%20usar%2FPortugu%C3%A9s%2Fnombres_portugues.txt?alt=media&token=e985f4ef-ea27-4d95-8738-8614f8b81c1b"
        url_lugares_pt = "https://firebasestorage.googleapis.com/v0/b/fastest-e5579.appspot.com/o/Archivos%20para%20usar%2FPortugu%C3%A9s%2Flugares_portu_defi.txt?alt=media&token=e2b72961-551a-4c7d-a340-e9daaee778af"
        url_verbos_pt = "https://firebasestorage.googleapis.com/v0/b/fastest-e5579.appspot.com/o/Archivos%20para%20usar%2FPortugu%C3%A9s%2Fverbos_portuges.txt?alt=media&token=6cedf5a2-d2c0-4d95-b0ec-c8711f89fba7"

        stopwords_lista_r_pt = requests.get(url_stopwords_pt)
        nombres_propios_lista_r_pt = requests.get(url_nombres_pt)
        lugares_lista_r_pt = requests.get(url_lugares_pt)
        verbos_lista_r_pt = requests.get(url_verbos_pt)

        stopwords_lista_r_pt.encoding = "utf-8"
        nombres_propios_lista_r_pt.encoding = "utf-8"
        lugares_lista_r_pt.encoding = "utf-8"
        verbos_lista_r_pt.encoding = "utf-8"

        stopwords_lista_url = stopwords_lista_r_pt.text.replace(
            "\r", "").split("\n")
        verbos_lista_url = verbos_lista_r_pt.text.replace(
            "\r", "").split("\n")
        verbos_conjugados_lista_url = verbos_lista_r_pt.text.replace(
            "\r", "").split("\n")
        apellidos_lista_url = []
        nombres_propios_lista_url = nombres_propios_lista_r_pt.text.replace(
            "\r", "").split("\n")
        lugares_lista_url = lugares_lista_r_pt.text.replace(
            "\r", "").split("\n")

    #                                                            Hacemos las preguntas:

    # Preguntas enumeraciones:
    startTime01 = time.time()
    preguntas_enumeraciones_dict = {}
    try:
        preguntas_enumeraciones_aux = preguntas_enumeraciones(texto_lineas)

        # Si ha cogido más de 5 preguntas lo dejamos solo en 5 preguntas aleatorias:
        if len(preguntas_enumeraciones_aux) > 5:
            lista_aux = [0, 1, 2, 3, 4]
            lista_keys = list(preguntas_enumeraciones_aux.keys())
            shuffle(lista_keys)
            for i in lista_aux:
                preguntas_enumeraciones_dict[i] = preguntas_enumeraciones_aux[lista_keys[i]]
        else:
            preguntas_enumeraciones_dict = preguntas_enumeraciones_aux

        # Sumamos las preguntas que hemos hecho al contador total:
        contador_total += len(preguntas_enumeraciones_dict)
        print(
            f'Preguntas enumeraciones hechas. Ha tardado {str(time.time() - startTime01)} segundos'+". Ha cogido estas preguntas: "+str(len(preguntas_enumeraciones_dict.keys())))
    except:
        print("No se crearon las preguntas de enumeraciones.")

    # Preguntas de nombres propios:
    startTime3 = time.time()
    preguntas_nombres_propios_dict = {}
    try:
        lista_aux = preguntas_nombres_propios(
            texto_leido, idioma)
        preguntas_nombres_propios_dict = lista_aux[0]
        texto_leido = lista_aux[1]

        # Sumamos las preguntas que hemos hecho al contador total:
        contador_total += len(preguntas_nombres_propios_dict)

        print(
            f'Preguntas nombres propios hechas. Ha tardado {str(time.time() - startTime3)} segundos'+". Ha cogido estas preguntas: "+str(len(preguntas_nombres_propios_dict.keys())))
        # print("Texto siguiente nombres: "+str(len(texto_leido)))
    except Exception as error:
        print("errorcito nombres: "+str(error))
        print('No se crearon las preguntas de nombres propios.')

    # Preguntas de lugares:
    startTime4 = time.time()
    preguntas_lugares_dict = {}
    try:
        lista_aux = preguntas_lugares(
            texto_leido, idioma)
        preguntas_lugares_dict = lista_aux[0]
        texto_leido = lista_aux[1]

        # Sumamos las preguntas que hemos hecho al contador total:
        contador_total += len(preguntas_lugares_dict)
        print(
            f'Preguntas lugares hechas. Ha tardado {str(time.time() - startTime4)} segundos'+". Ha cogido estas preguntas: "+str(len(preguntas_lugares_dict.keys())))
        # print("Texto siguiente lugares: "+str(len(texto_leido)))
    except Exception as error:
        print("errorcito lugares: "+str(error))
        print('No se crearon las preguntas de lugares.')

    # Preguntas de fechas:
    startTime5 = time.time()
    preguntas_fechas_dict = {}
    try:
        lista_aux = preguntas_fechas(
            texto_leido, idioma)
        preguntas_fechas_dict = lista_aux[0]
        texto_leido = lista_aux[1]

        # Sumamos las preguntas que hemos hecho al contador total:
        contador_total += len(preguntas_fechas_dict)
        print(
            f'Preguntas fechas hechas. Ha tardado {str(time.time() - startTime5)} segundos'+". Ha cogido estas preguntas: "+str(len(preguntas_fechas_dict.keys())))
        # print("Texto siguiente fechas: "+str(len(texto_leido)))
    except:
        print('No se crearon las preguntas de fechas.')

    # Preguntas dos puntos:
    startTime6 = time.time()
    preguntas_dos_puntos_dict = {}
    try:
        # Comprobamos cuántas preguntas llevamos ya para ponerle el límite:
        preguntas_hacer_dos_puntos = lim_total_con_reserva - contador_total

        if preguntas_hacer_dos_puntos > 20:
            preguntas_hacer_dos_puntos = 20

        lista_aux = preguntas_dos_puntos(
            texto_leido, preguntas_hacer_dos_puntos)
        preguntas_dos_puntos_dict = lista_aux[0]
        texto_leido = lista_aux[1]

        # Sumamos las preguntas que hemos hecho al contador total:
        contador_total += len(preguntas_dos_puntos_dict)
        print(
            f'Preguntas dos puntos hechas. Ha tardado {str(time.time() - startTime6)} segundos'+". Ha cogido estas preguntas: "+str(len(preguntas_dos_puntos_dict.keys())))
        # print("Texto siguiente dos puntos: "+str(len(texto_leido)))
    except:
        print('No se crearon las preguntas de dos puntos.')

    # Preguntas mayúsculas:
    startTime7 = time.time()
    preguntas_mayusculas_dict = {}
    try:
        # Comprobamos cuántas preguntas llevamos ya para ponerle el límite:
        preguntas_hacer_mayusculas = lim_total_con_reserva - contador_total

        # En la última pregunta no hace falta ya pasar el texto sin las frases que has usado
        preguntas_mayusculas_dict = preguntas_mayusculas(
            texto_leido, preguntas_hacer_mayusculas)
        print(
            f'Preguntas mayusculas hechas. Ha tardado {str(time.time() - startTime7)} segundos'+". Ha cogido estas preguntas: "+str(len(preguntas_mayusculas_dict.keys())))
    except:
        print('No se crearon las preguntas de mayusculas.')

    # # Preguntas rellenar huecos con keywords (en principio no funcionan):
    # startTime2 = time.time()
    preguntas_rellenar_huecos_keywords_dict = {}

    # try:
    #     preguntas_rellenar_huecos_keywords_dict = preguntas_rellenar_keywords(
    #         texto_leido)

    #     print(
    #         f'Preguntas rellenar keywords hechas. Ha tardado {str(time.time() - startTime2)} segundos'+". Ha cogido estas preguntas: "+str(len(preguntas_rellenar_huecos_keywords_dict.keys())))
    # except:
    #     print('No se crearon las preguntas rellenar huecos con keywords.')
    #

    #                                                  Añadimos las preguntas:

    args_dict['preguntas_enumeraciones'] = preguntas_enumeraciones_dict
    args_dict['preguntas_rellenar_huecos_keywords'] = preguntas_rellenar_huecos_keywords_dict
    args_dict['preguntas_nombres_propios'] = preguntas_nombres_propios_dict
    args_dict['preguntas_lugares'] = preguntas_lugares_dict
    args_dict['preguntas_fechas'] = preguntas_fechas_dict
    args_dict['preguntas_dos_puntos'] = preguntas_dos_puntos_dict
    args_dict['preguntas_mayusculas'] = preguntas_mayusculas_dict

    # Borramos el archivo de cloud storage:
    try:
        storage.child(pdf_path).delete(pdf_path)
        print('Se ha borrado el archivo del storage.')
    except:
        print('No se ha podido borrar el archivo del storage.')

    totalTime = (time.time() - startTime)
    print('Ha tardado ' + str(totalTime)+' segundos en hacer todo')

    return args_dict
