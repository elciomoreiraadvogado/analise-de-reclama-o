import os
from collections import Counter
from flask import Flask, jsonify, render_template, request
from nltk import FreqDist
from nltk.tokenize import RegexpTokenizer

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024

TOKENIZER = RegexpTokenizer(r"[A-Za-zÀ-ÖØ-öø-ÿ]+(?:-[A-Za-zÀ-ÖØ-öø-ÿ]+)*")

STOPWORDS_BASE = set("""
a à ao aos aquela aquelas aquele aqueles aquilo as até com como da das de dela delas dele deles depois do dos
e é ela elas ele eles em entre era eram essa essas esse esses esta estas este estes estou está estão eu foi foram
for fui há isso isto já lhe lhes mais mas me mesmo meu meus minha minhas muito na nas nem no nos nós nossa nossas
nosso nossos num numa o os ou para pela pelas pelo pelos por qual quando que quem se sem ser seu seus só sua suas
também te tem têm tinha tive um uma umas uns você vocês vos ter foi estar fazer faz fez pra pro tá né aí ali lá aqui
sobre ainda então porque porém pois só sempre nunca já vez ficou coisa bem mal tudo todo toda todos todas
""".split())

def carregar_stopwords():
    palavras = set(STOPWORDS_BASE)
    try:
        from nltk.corpus import stopwords
        palavras |= set(stopwords.words("portuguese"))
    except (LookupError, OSError):
        try:
            import nltk
            if nltk.download("stopwords", quiet=True):
                from nltk.corpus import stopwords
                palavras |= set(stopwords.words("portuguese"))
        except Exception:
            pass
    return palavras

STOPWORDS = carregar_stopwords()

def analisar(texto, top_n=15, min_len=3, remover_stopwords=True):
    tokens = [t.lower() for t in TOKENIZER.tokenize(texto)]
    total = len(tokens)
    tokens = [t for t in tokens if len(t) >= min_len]
    if remover_stopwords:
        tokens = [t for t in tokens if t not in STOPWORDS]

    freq = FreqDist(tokens)
    mais_comuns = freq.most_common(top_n)
    maximo = mais_comuns[0][1] if mais_comuns else 1
    resultado = [
        {
            "palavra": palavra,
            "ocorrencias": qtd,
            "percentual": round(qtd / len(tokens) * 100, 1) if tokens else 0,
            "barra": round(qtd / maximo * 100),
        }
        for palavra, qtd in mais_comuns
    ]
    return {
        "total_palavras": total,
        "palavras_relevantes": len(tokens),
        "palavras_unicas": len(freq),
        "ranking": resultado,
    }

def ler_parametros(origem):
    try:
        top_n = max(5, min(int(origem.get("top_n", 15)), 50))
    except (TypeError, ValueError):
        top_n = 15
    remover = origem.get("remover_stopwords", "on") in ("on", "true", True, "1")
    return top_n, remover

@app.route("/", methods=["GET", "POST"])
def index():
    texto, resultado, erro = "", None, None
    top_n, remover = 15, True
    if request.method == "POST":
        texto = request.form.get("texto", "").strip()
        top_n, _ = ler_parametros(request.form)
        remover = request.form.get("remover_stopwords") == "on"
        if len(texto) < 10:
            erro = "Informe um texto de reclamação com pelo menos 10 caracteres."
        else:
            resultado = analisar(texto, top_n=top_n, remover_stopwords=remover)
            if not resultado["ranking"]:
                erro = "Nenhuma palavra relevante encontrada no texto informado."
                resultado = None
    return render_template("index.html", texto=texto, resultado=resultado, erro=erro, top_n=top_n, remover=remover)

@app.route("/api/analisar", methods=["POST"])
def api_analisar():
    dados = request.get_json(silent=True) or {}
    texto = (dados.get("texto") or "").strip()
    if len(texto) < 10:
        return jsonify(erro="Campo 'texto' obrigatório (mín. 10 caracteres)."), 400
    top_n, remover = ler_parametros(dados)
    return jsonify(analisar(texto, top_n=top_n, remover_stopwords=remover))

@app.route("/saude")
def saude():
    return jsonify(status="ok")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)