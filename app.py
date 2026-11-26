import os

from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from flask_wtf.csrf import CSRFProtect
from mysql.connector import Error
from werkzeug.security import check_password_hash

from db import execute_insert, execute_one, execute_query

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Liga a proteção CSRF: todo formulário POST do sistema vai precisar do token
CSRFProtect(app)

# ==============================================================================
# PÁGINAS PRINCIPAIS
# ==============================================================================

@app.route('/')
def index():
    # A raiz não mostra nada: só leva para a tela de login
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Quem já entrou não precisa ver a tela de login
    if 'id_usuario' in session:
        return redirect(url_for('dashboard'))

    email = ''

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')

        # Só o login lê a coluna senha (o hash)
        usuario = execute_one(
            'SELECT u.id_usuario, u.nome, u.senha, p.nome AS perfil '
            'FROM usuarios u '
            'JOIN perfis p ON p.id_perfil = u.perfil_id '
            'WHERE u.email = %s',
            (email,),
        )

        if usuario is not None and check_password_hash(usuario['senha'], senha):
            # Guarda na session quem entrou (o cookie assinado pela secret_key)
            session.clear()
            session['id_usuario'] = usuario['id_usuario']
            session['nome'] = usuario['nome']
            session['perfil'] = usuario['perfil']
            flash(f'Você entrou como {usuario["nome"]}.', 'success')
            return redirect(url_for('dashboard'))

        # A mesma mensagem para e-mail inexistente e senha errada
        flash('E-mail ou senha incorretos.', 'danger')

    return render_template('login.html', email=email)


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash('Você saiu do sistema.', 'success')

    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'id_usuario' not in session:
        flash('Entre para continuar.', 'warning')
        return redirect(url_for('login'))

    # Conta as linhas de cada tabela para os cartões do painel
    perfis = execute_one('SELECT COUNT(*) AS total FROM perfis')
    pets = execute_one('SELECT COUNT(*) AS total FROM pets')
    servicos = execute_one('SELECT COUNT(*) AS total FROM servicos')

    return render_template('dashboard.html',
                           total_perfis=perfis['total'],
                           total_pets=pets['total'],
                           total_servicos=servicos['total'])


# ==============================================================================
# BUSCA (campo "Procurar" do menu)
# ==============================================================================

@app.route('/busca')
def busca():
    if 'id_usuario' not in session:
        flash('Entre para continuar.', 'warning')
        return redirect(url_for('login'))

    termo = request.args.get('q', '').strip()
    achados_pets = []
    achados_servicos = []

    if termo:
        # O % do LIKE vai junto do valor, nunca dentro do SQL
        parecido = '%' + termo + '%'
        achados_pets = execute_query('SELECT * FROM pets WHERE nome LIKE %s',
                                     (parecido,), fetch=True)
        achados_servicos = execute_query('SELECT * FROM servicos WHERE nome LIKE %s',
                                         (parecido,), fetch=True)

    return render_template('busca.html', termo=termo, pets=achados_pets, servicos=achados_servicos)


# ==============================================================================
# PERFIL
# ==============================================================================

@app.route("/perfis/inserir", methods=["GET", "POST"])
def inserir_perfil():

    nome = ""
    descricao = ""

    if request.method == "POST":
        nome = request.form.get("nome").strip()
        descricao = request.form.get("descricao").strip()

        try:
            novo_id = execute_insert(
               'INSERT INTO perfis (nome, descricao) VALUES(%s,%s)',
               (nome, descricao)
            )
            flash(f"Perfil {nome} cadastro com o ID: {novo_id}", "success")
            return redirect(url_for("listar_perfis"))

        except Error as erro:
            if erro.errno == 1062:
                flash("Já existe um perfil com este nome", "danger")
            else:
                raise

    return render_template("perfis/perfil-form.html", nome=nome, descricao=descricao)

@app.route("/perfis")
def listar_perfis():
    perfis = execute_query(
        'SELECT id_perfil, nome, descricao, criado_em FROM perfis ORDER BY nome',
        fetch=True
    )

    return render_template("perfis/perfis-listar.html", perfis=perfis)


# ==============================================================================
# PETS
# ==============================================================================

def coletar_pet():
    return {
        'nome': request.form.get('nome', '').strip(),
        'especie': request.form.get('especie', ''),
        'raca': request.form.get('raca', '').strip() or None,
        'porte': request.form.get('porte', '') or None,
        'data_nascimento': request.form.get('data_nascimento', '').strip() or None,
        # Aceita 32,5 ou 32.5: o banco usa ponto
        'peso': request.form.get('peso', '').strip().replace(',', '.') or None,
        'tutor': request.form.get('tutor', '').strip(),
        'observacoes': request.form.get('observacoes', '').strip() or None,
    }


def validar_pet(pet):
    erros = []
    if not pet['nome']:
        erros.append('O nome do pet é obrigatório.')
    if not pet['especie']:
        erros.append('Escolha a espécie.')
    if not pet['tutor']:
        erros.append('O nome do tutor é obrigatório.')
    if pet['peso']:
        try:
            float(pet['peso'])
        except ValueError:
            erros.append('Digite um peso válido.')
    return erros


def dados_pet(pet):
    # Os valores na mesma ordem das colunas do INSERT e do UPDATE
    return (pet['nome'], pet['especie'], pet['raca'], pet['porte'],
            pet['data_nascimento'], pet['peso'], pet['tutor'], pet['observacoes'])


@app.route('/pets')
def listar_pets():
    if 'id_usuario' not in session:
        flash('Entre para continuar.', 'warning')
        return redirect(url_for('login'))

    pets = execute_query('SELECT * FROM pets ORDER BY nome', fetch=True)
    return render_template('pet_lista.html', pets=pets)


@app.route('/pets/inserir', methods=['GET', 'POST'])
def inserir_pet():
    if 'id_usuario' not in session:
        flash('Entre para continuar.', 'warning')
        return redirect(url_for('login'))

    pet = {}

    if request.method == 'POST':
        pet = coletar_pet()
        erros = validar_pet(pet)

        if erros:
            for mensagem in erros:
                flash(mensagem, 'danger')
        else:
            execute_insert(
                'INSERT INTO pets (nome, especie, raca, porte, data_nascimento, peso, '
                'tutor, observacoes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                dados_pet(pet))
            flash(f'Pet "{pet["nome"]}" cadastrado.', 'success')
            return redirect(url_for('listar_pets'))

    return render_template('pet_form.html', acao='criar', id_pet=None, pet=pet)


@app.route('/pets/<int:id_pet>/editar', methods=['GET', 'POST'])
def editar_pet(id_pet):
    if 'id_usuario' not in session:
        flash('Entre para continuar.', 'warning')
        return redirect(url_for('login'))

    pet = execute_one('SELECT * FROM pets WHERE id_pet = %s', (id_pet,))
    if pet is None:
        abort(404)

    if request.method == 'POST':
        pet = coletar_pet()
        erros = validar_pet(pet)

        if erros:
            for mensagem in erros:
                flash(mensagem, 'danger')
        else:
            execute_query(
                'UPDATE pets SET nome = %s, especie = %s, raca = %s, porte = %s, '
                'data_nascimento = %s, peso = %s, tutor = %s, observacoes = %s '
                'WHERE id_pet = %s',
                dados_pet(pet) + (id_pet,))
            flash(f'Pet "{pet["nome"]}" atualizado.', 'success')
            return redirect(url_for('listar_pets'))

    return render_template('pet_form.html', acao='editar', id_pet=id_pet, pet=pet)


@app.route('/pets/<int:id_pet>/excluir', methods=['POST'])
def excluir_pet(id_pet):
    if 'id_usuario' not in session:
        flash('Entre para continuar.', 'warning')
        return redirect(url_for('login'))

    execute_query('DELETE FROM pets WHERE id_pet = %s', (id_pet,))
    flash('Pet excluído.', 'success')
    return redirect(url_for('listar_pets'))


# ==============================================================================
# SERVIÇOS
# ==============================================================================

def coletar_servico():
    return {
        'nome': request.form.get('nome', '').strip(),
        'descricao': request.form.get('descricao', '').strip() or None,
        'preco': request.form.get('preco', '').strip().replace(',', '.'),
        'duracao_minutos': request.form.get('duracao_minutos', '').strip(),
        # Checkbox desmarcado não é enviado (aula 4)
        'ativo': 1 if request.form.get('ativo') else 0,
    }


def validar_servico(servico):
    erros = []
    if not servico['nome']:
        erros.append('O nome do serviço é obrigatório.')
    try:
        float(servico['preco'])
    except ValueError:
        erros.append('Digite um preço válido.')
    # Tudo o que chega do formulário é texto: precisa ser um número inteiro
    try:
        duracao = int(servico['duracao_minutos'])
        if duracao <= 0:
            erros.append('A duração deve ser maior que zero.')
    except ValueError:
        erros.append('A duração deve ser um número de minutos.')
    return erros


def dados_servico(servico):
    return (servico['nome'], servico['descricao'], servico['preco'],
            servico['duracao_minutos'], servico['ativo'])


@app.route('/servicos')
def listar_servicos():
    if 'id_usuario' not in session:
        flash('Entre para continuar.', 'warning')
        return redirect(url_for('login'))

    servicos = execute_query('SELECT * FROM servicos ORDER BY nome', fetch=True)
    return render_template('servico_lista.html', servicos=servicos)


@app.route('/servicos/inserir', methods=['GET', 'POST'])
def inserir_servico():
    if 'id_usuario' not in session:
        flash('Entre para continuar.', 'warning')
        return redirect(url_for('login'))

    servico = {'ativo': 1}

    if request.method == 'POST':
        servico = coletar_servico()
        erros = validar_servico(servico)

        if erros:
            for mensagem in erros:
                flash(mensagem, 'danger')
        else:
            execute_insert(
                'INSERT INTO servicos (nome, descricao, preco, duracao_minutos, ativo) '
                'VALUES (%s, %s, %s, %s, %s)',
                dados_servico(servico))
            flash(f'Serviço "{servico["nome"]}" cadastrado.', 'success')
            return redirect(url_for('listar_servicos'))

    return render_template('servico_form.html', acao='criar', id_servico=None, servico=servico)


@app.route('/servicos/<int:id_servico>/editar', methods=['GET', 'POST'])
def editar_servico(id_servico):
    if 'id_usuario' not in session:
        flash('Entre para continuar.', 'warning')
        return redirect(url_for('login'))

    servico = execute_one('SELECT * FROM servicos WHERE id_servico = %s', (id_servico,))
    if servico is None:
        abort(404)

    if request.method == 'POST':
        servico = coletar_servico()
        erros = validar_servico(servico)

        if erros:
            for mensagem in erros:
                flash(mensagem, 'danger')
        else:
            execute_query(
                'UPDATE servicos SET nome = %s, descricao = %s, preco = %s, '
                'duracao_minutos = %s, ativo = %s WHERE id_servico = %s',
                dados_servico(servico) + (id_servico,))
            flash(f'Serviço "{servico["nome"]}" atualizado.', 'success')
            return redirect(url_for('listar_servicos'))

    return render_template('servico_form.html', acao='editar', id_servico=id_servico,
                           servico=servico)


@app.route('/servicos/<int:id_servico>/excluir', methods=['POST'])
def excluir_servico(id_servico):
    if 'id_usuario' not in session:
        flash('Entre para continuar.', 'warning')
        return redirect(url_for('login'))

    execute_query('DELETE FROM servicos WHERE id_servico = %s', (id_servico,))
    flash('Serviço excluído.', 'success')
    return redirect(url_for('listar_servicos'))


# ==============================================================================
# TELAS DE ERROS
# ==============================================================================

@app.errorhandler(404)
def pagina_nao_encontrada(erro):
    return render_template('404.html'), 404


@app.errorhandler(500)
def erro_no_servidor(erro):
    return render_template('500.html'), 500

if __name__ == "__main__":
    app.run(debug=True)
