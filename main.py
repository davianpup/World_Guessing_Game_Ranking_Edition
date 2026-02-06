import sqlite3
import requests
import random
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
from datetime import datetime
import time

contador = 0

class BancoDados:
    def __init__(self, nome_banco="ranking_paises.db"):
        self.conexao = sqlite3.connect(nome_banco)
        self.criar_tabela()

    def criar_tabela(self):
        cursor = self.conexao.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ranking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jogador TEXT NOT NULL,
                pontuacao INTEGER NOT NULL,
                data_hora TEXT NOT NULL
            )
        ''')
        self.conexao.commit()

    def salvar_ranking(self, jogador, pontuacao):
        cursor = self.conexao.cursor()
        cursor.execute(
            "INSERT INTO ranking (jogador, pontuacao, data_hora) VALUES (?, ?, ?)",
            (jogador, pontuacao, datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        )
        self.conexao.commit()

    def buscar_ranking(self):
        cursor = self.conexao.cursor()
        cursor.execute(
            "SELECT jogador, pontuacao, data_hora FROM ranking ORDER BY pontuacao DESC LIMIT 10"
        )
        return cursor.fetchall()

class ServicoAPI:
    def __init__(self):
        self.url = "https://restcountries.com/v3.1/all?fields=name,capital,population,flags,translations,continents"
        self.traducao_continentes = {
            "South America": "América do Sul", "North America": "América do Norte",
            "Europe": "Europa", "Africa": "África", "Asia": "Ásia",
            "Oceania": "Oceania", "Antarctica": "Antártida"
        }

    def buscar_pais(self):
        try:
            resposta = requests.get(self.url)
            resposta.raise_for_status()
            lista_paises = resposta.json()
            paises_validos = [p for p in lista_paises if 'capital' in p and 'name' in p]
            pais = random.choice(paises_validos)
            try:
                nome_pt = pais['translations']['por']['common']
            except:
                nome_pt = pais['name']['common']
            continente_ingles = pais.get('continents', ['Desconhecido'])[0]
            continente_pt = self.traducao_continentes.get(continente_ingles, continente_ingles)
            populacao = pais.get('population', 0)
            return {
                "nome": nome_pt,
                "capital": pais['capital'][0],
                "continente": continente_pt,
                "populacao": populacao
            }
        except Exception as e:
            print(f"Erro: {e}")
            return None

api = ServicoAPI()
banco = BancoDados()

class AppJogo(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Adivinhe o País")
        self.geometry("600x500")
        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)
        self.dados_pais = None
        self.segundos = 0
        self.timer_ativo = False
        self.tela_titulo()

    def limpar_tela(self):
        self.timer_ativo = False
        for widget in self.container.winfo_children():
            widget.destroy()

    def atualizar_timer(self):
        if self.timer_ativo:
            self.segundos += 1
            self.label_timer.config(text=f"Tempo: {self.segundos}s")
            self.after(1000, self.atualizar_timer)

    def tela_titulo(self):
        self.limpar_tela()
        tk.Label(self.container, text="Adivinhe o País!", font=("Arial", 24, "bold")).pack(pady=20)
        tk.Label(self.container, text="Grupo: Davi Ângelo, Gabriel Avelino, Gabriel Felipe", font=("Arial", 10)).pack()
        tk.Button(self.container, text="JOGAR", width=20, height=2, bg="green", fg="white",
                  command=self.tela_jogar).pack(pady=10)
        tk.Button(self.container, text="RANKING", width=20, command=self.tela_ranking).pack(pady=5)

    def tela_jogar(self):
        self.limpar_tela()
        self.dados_pais = api.buscar_pais()
        if not self.dados_pais:
            messagebox.showerror("Erro", "Erro ao conectar com a API!")
            self.tela_titulo()
            return
        self.segundos = 0
        self.timer_ativo = True
        self.label_timer = tk.Label(self.container, text="Tempo: 0s", font=("Arial", 12, "bold"), fg="red")
        self.label_timer.pack(pady=5)
        self.atualizar_timer()
        tk.Label(self.container, text="Qual é o país?", font=("Arial", 18)).pack(pady=10)
        frame_dicas = tk.LabelFrame(self.container, text="Dicas", padx=10, pady=10)
        frame_dicas.pack(pady=10)
        tk.Button(frame_dicas, text="Ver Capital", width=15,
                  command=lambda: messagebox.showinfo("Dica", f"A capital é: {self.dados_pais['capital']}")).pack(pady=2)
        tk.Button(frame_dicas, text="Ver Continente", width=15,
                  command=lambda: messagebox.showinfo("Dica", f"Fica na: {self.dados_pais['continente']}")).pack(pady=2)
        self.entrada = tk.Entry(self.container, font=("Arial", 16), justify="center")
        self.entrada.pack(pady=10)
        self.entrada.focus_set()
        self.bind('<Return>', lambda event: self.verificar_resposta())
        tk.Button(self.container, text="Confirmar!", width=20, bg="blue", fg="white",
                  command=self.verificar_resposta).pack(pady=5)
        tk.Button(self.container, text="Desistir / Voltar", command=self.tela_titulo).pack(pady=20)

    def calcular_pontuacao(self, segundos, populacao):
        total_segundos = int(segundos)
        hora = total_segundos // 3600
        minuto = (total_segundos % 3600) // 60
        seg2 = total_segundos % 60
        if hora == 0 and minuto == 0 and 1 <= seg2 <= 5:
            pontuacao = 1000
        elif hora == 0 and minuto == 0 and 6 <= seg2 <= 30:
            pontuacao = 850
        elif hora == 0 and minuto == 0 and 31 <= seg2 <= 59:
            pontuacao = 700
        elif hora == 0 and 1 <= minuto <= 30:
            pontuacao = 500
        elif hora >= 1:
            pontuacao = 100
        else:
            pontuacao = 700
        try:
            if populacao <= 50000:
                pontuacao = pontuacao * 2
        except Exception:
            pass
        return pontuacao

    def verificar_resposta(self):
        chute = self.entrada.get().strip().lower()
        correto = self.dados_pais['nome'].lower()
        if chute == correto:
            self.timer_ativo = False
            populacao = self.dados_pais.get('populacao', 0)
            pontuacao = self.calcular_pontuacao(self.segundos, populacao)
            salvar = messagebox.askyesno(
                "ACERTOU!",
                f"Parabéns! Você levou {self.segundos} segundos.\n"
                f"O país era {self.dados_pais['nome']}!\n\n"
                f"Sua pontuação: {pontuacao}\n\n"
                "Deseja salvar seu resultado no ranking?"
            )
            if salvar:
                nome = simpledialog.askstring("Ranking", "Digite seu nome:")
                if nome:
                    banco.salvar_ranking(nome, pontuacao)
            self.tela_jogar()
        else:
            messagebox.showerror("ERROU", "Tente novamente ou peça uma dica!")

    def tela_ranking(self):
        self.limpar_tela()
        tk.Label(self.container, text="🏆 Ranking", font=("Arial", 22, "bold")).pack(pady=20)
        dados = banco.buscar_ranking()
        if not dados:
            tk.Label(self.container, text="Nenhum registro ainda.", font=("Arial", 12)).pack(pady=10)
        else:
            tabela = ttk.Treeview(self.container, columns=("Jogador", "Pontuação", "Data"), show="headings")
            tabela.heading("Jogador", text="Jogador")
            tabela.heading("Pontuação", text="Pontuação")
            tabela.heading("Data", text="Data/Hora")
            tabela.column("Jogador", anchor="center", width=180)
            tabela.column("Pontuação", anchor="center", width=120)
            tabela.column("Data", anchor="center", width=200)
            for jogador, pontuacao, data in dados:
                tabela.insert("", "end", values=(jogador, pontuacao, data))
            tabela.pack(pady=10)
        tk.Button(self.container, text="Voltar", command=self.tela_titulo).pack(pady=20)

if __name__ == "__main__":
    app = AppJogo()
    app.mainloop()