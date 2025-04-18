from flask import Flask, render_template, request, redirect, url_for
from models import Intervento, session
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def home():
    interventi = session.query(Intervento).order_by(Intervento.data.desc()).all()
    return render_template("index.html", interventi=interventi)

@app.route("/aggiungi", methods=["GET", "POST"])
def aggiungi():
    if request.method == "POST":
        nome = request.form["nome_cliente"]
        data = datetime.strptime(request.form["data"], "%Y-%m-%d").date()
        durata = float(request.form["durata_ore"])
        note = request.form["note"]
        risolto = "risolto" in request.form
        urgenza = "urgenza" in request.form
        signature = request.form.get("signature", "")

        costo = durata * 30
        if urgenza:
            costo += 20

        nuovo = Intervento(
            nome_cliente=nome,
            durata_ore=durata,
            data=data,
            note=note,
            risolto=risolto,
            urgenza=urgenza,
            costo_totale=costo,
            signature=signature
        )
        session.add(nuovo)
        session.commit()
        return redirect(url_for("home"))

    return render_template("aggiungi.html")

# ———————————
# ROUTE PER LA MODIFICA
@app.route("/modifica/<int:id>", methods=["GET", "POST"])
def modifica(id):
    intervento = session.query(Intervento).get(id)
    if not intervento:
        return redirect(url_for("home"))

    if request.method == "POST":
        intervento.nome_cliente = request.form["nome_cliente"]
        intervento.data = datetime.strptime(request.form["data"], "%Y-%m-%d").date()
        intervento.durata_ore = float(request.form["durata_ore"])
        intervento.note = request.form["note"]
        intervento.risolto = "risolto" in request.form
        intervento.urgenza = "urgenza" in request.form
        new_sig = request.form.get("signature", "")
        if new_sig:
            intervento.signature = new_sig

        # ricalcola il costo
        costo = intervento.durata_ore * 30
        if intervento.urgenza:
            costo += 20
        intervento.costo_totale = costo

        session.commit()
        return redirect(url_for("home"))

    return render_template("modifica.html", intervento=intervento)

# ———————————
# ROUTE PER L’ELIMINAZIONE
@app.route("/elimina/<int:id>", methods=["POST"])
def elimina(id):
    intervento = session.query(Intervento).get(id)
    if intervento:
        session.delete(intervento)
        session.commit()
    return redirect(url_for("home"))

@app.route("/statistiche")
def statistiche():
    interventi = session.query(Intervento).all()

    totale_ore = sum(i.durata_ore for i in interventi)
    guadagno_totale = sum(i.costo_totale for i in interventi)
    risolti = sum(1 for i in interventi if i.risolto)
    non_risolti = sum(1 for i in interventi if not i.risolto)
    urgenti = sum(1 for i in interventi if i.urgenza)
    totale_interventi = len(interventi)

    return render_template("stats.html",
        totale_ore=totale_ore,
        guadagno_totale=guadagno_totale,
        risolti=risolti,
        non_risolti=non_risolti,
        urgenti=urgenti,
        totale_interventi=totale_interventi
    )

if __name__ == "__main__":
    app.run(debug=True)
