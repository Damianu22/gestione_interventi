from flask import Flask, render_template, request, redirect, url_for, send_file
from models import Intervento, session
from datetime import datetime
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm


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
        tipo_pagamento = request.form["tipo_pagamento"]

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
            signature=signature,
            tipo_pagamento=tipo_pagamento
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
        intervento.tipo_pagamento = request.form["tipo_pagamento"]

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

@app.route("/invoice/<int:id>")
def invoice(id):
    intervento = session.query(Intervento).get(id)
    if not intervento:
        return redirect(url_for("home"))

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # --- Header ---
    p.setFont("Helvetica-Bold", 20)
    p.drawString(30*mm, (height - 30*mm), "FATTURA INTERVENTO TECNICO")
    # Linea sotto header
    p.setLineWidth(1)
    p.line(20*mm, (height - 32*mm), (width - 20*mm), (height - 32*mm))

    # --- Dati Cliente & Data ---
    p.setFont("Helvetica", 12)
    y = height - 45*mm
    p.drawString(30*mm, y, f"Cliente: {intervento.nome_cliente}")
    p.drawString(120*mm, y, f"Data: {intervento.data.strftime('%d/%m/%Y')}")
    # Linea di separazione
    p.line(20*mm, (y - 2*mm), (width - 20*mm), (y - 2*mm))

    # --- Tabella dettagli intervento ---
    y -= 12*mm
    p.setFont("Helvetica-Bold", 12)
    p.drawString(30*mm, y, "Descrizione")
    p.drawString(100*mm, y, "Quantità")
    p.drawString(130*mm, y, "Prezzo Unitario")
    p.drawString(170*mm, y, "Totale")
    y -= 5*mm
    p.setLineWidth(0.5)
    p.line(20*mm, y, (width - 20*mm), y)

    # Righe di dati
    p.setFont("Helvetica", 12)
    y -= 7*mm
    # Intervento tecnico
    descr = "Intervento tecnico"
    qty = f"{intervento.durata_ore:.2f} h"
    unit = "30,00 €"
    total = f"{intervento.durata_ore * 30:.2f} €"
    p.drawString(30*mm, y, descr)
    p.drawString(100*mm, y, qty)
    p.drawString(130*mm, y, unit)
    p.drawString(170*mm, y, total)
    y -= 7*mm

    # Urgenza
    if intervento.urgenza:
        qty = "–"
        unit = "+20,00 €"
        total = "20,00 €"
        p.drawString(30*mm, y, "Servizio urgente")
        p.drawString(100*mm, y, qty)
        p.drawString(130*mm, y, unit)
        p.drawString(170*mm, y, total)
        y -= 7*mm

    # Linea sotto tabella
    p.line(20*mm, (y - 2*mm), (width - 20*mm), (y - 2*mm))


    # --- Totale complessivo + Metodo di pagamento sulla stessa riga ---
    y -= 12*mm
    p.setFont("Helvetica-Bold", 12)
    p.drawString(30*mm, y, f"Metodo di pagamento: {intervento.tipo_pagamento}")
    p.drawRightString((width - 20*mm), y, f"Importo totale: {intervento.costo_totale:.2f} €")


    # --- Footer ---
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(30*mm, 20*mm, "Grazie per averci scelto! Per info chiamare Marco al +39 339 588 0581")

    p.showPage()
    p.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"fattura_{intervento.id}.pdf",
        mimetype="application/pdf"
    )

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


