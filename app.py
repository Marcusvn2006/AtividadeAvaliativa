import os

from dotenv import load_dotenv
from flask import Flask, abort, flash, render_template, request, redirect, url_for
from flask_wtf.csrf import CSRFProtect
from mysql.connector import Error

from db import execute_insert, execute_one, execute_query

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Liga a proteção CSRF: todo formulário POST do sistema vai precisar do token
CSRFProtect(app)


# LOGIN E PAINEL

# Credenciais fixas, só para a atividade
LOGIN_EMAIL = 'admin@petfeliz.com'
LOGIN_SENHA = '123456'

@app.route('/', methods=['GET', 'POST'])
def login():
    erros = []
    email = ''

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '').strip()

        if not email:
            erros.append('O e-mail é obrigatório.')
        if not senha:
            erros.append('A senha é obrigatória.')

        # Campos preenchidos: confere e-mail e senha
        if not erros:
            if email == LOGIN_EMAIL and senha == LOGIN_SENHA:
                return redirect(url_for('dashboard'))
            erros.append('E-mail ou senha incorretos.')

    return render_template('login.html', email=email, erros=erros)


@app.route('/dashboard')
def dashboard():
    # Conta as linhas de cada tabela para os cartões do painel
    usuarios = execute_one('SELECT COUNT(*) AS total FROM usuarios')
    pets = execute_one('SELECT COUNT(*) AS total FROM pets')
    servicos = execute_one('SELECT COUNT(*) AS total FROM servicos')

    return render_template('dashboard.html',
                           total_usuarios=usuarios['total'],
                           total_pets=pets['total'],
                           total_servicos=servicos['total'])


# BUSCA (campo "Procurar" do menu)

@app.route('/busca')
def busca():
    termo = request.args.get('q', '').strip()
    achados_usuarios = []
    achados_pets = []
    achados_servicos = []

    if termo:
        # O % do LIKE vai junto do valor, nunca dentro do SQL
        parecido = '%' + termo + '%'
        achados_usuarios = execute_query('SELECT * FROM usuarios WHERE nome LIKE %s',
                                         (parecido,), fetch=True)
        achados_pets = execute_query('SELECT * FROM pets WHERE nome LIKE %s',
                                     (parecido,), fetch=True)
        achados_servicos = execute_query('SELECT * FROM servicos WHERE nome LIKE %s',
                                         (parecido,), fetch=True)

    return render_template('busca.html', termo=termo, usuarios=achados_usuarios,
                           pets=achados_pets, servicos=achados_servicos)


# USUÁRIOS

@app.route('/usuarios')
def lista_usuarios():
    usuarios = execute_query('SELECT * FROM usuarios ORDER BY nome', fetch=True)
    return render_template('usuario_lista.html', usuarios=usuarios)


@app.route('/usuarios/cadastro', methods=['GET', 'POST'])
@app.route('/usuarios/<int:id_usuario>/editar', methods=['GET', 'POST'])
def cadastro_usuario(id_usuario=None):
    usuario = {}
    erros = []

    # Editando: busca o usuário no banco para preencher o formulário
    if id_usuario:
        usuario = execute_one('SELECT * FROM usuarios WHERE id_usuario = %s', (id_usuario,))
        if usuario is None:
            abort(404)

    if request.method == 'POST':
        # "or None": campo vazio vira NULL no banco
        usuario.update({
            'nome': request.form.get('nome', '').strip(),
            'email': request.form.get('email', '').strip(),
            'celular': request.form.get('celular', '').strip() or None,
            'data_nascimento': request.form.get('data_nascimento', '').strip() or None,
            'cpf': request.form.get('cpf', '').strip() or None,
            'nivel_acesso': request.form.get('nivel_acesso', ''),
            'cep': request.form.get('cep', '').strip() or None,
            'endereco': request.form.get('endereco', '').strip() or None,
            'numero': request.form.get('numero', '').strip() or None,
            'complemento': request.form.get('complemento', '').strip() or None,
            'cidade': request.form.get('cidade', '').strip() or None,
        })

        if len(usuario['nome']) < 3:
            erros.append('O nome deve ter pelo menos 3 caracteres.')
        if '@' not in usuario['email']:
            erros.append('Digite um e-mail válido.')
        if not usuario['nivel_acesso']:
            erros.append('Escolha o nível de acesso.')

        if not erros:
            dados = (usuario['nome'], usuario['email'], usuario['celular'],
                     usuario['data_nascimento'], usuario['cpf'], usuario['nivel_acesso'],
                     usuario['cep'], usuario['endereco'], usuario['numero'],
                     usuario['complemento'], usuario['cidade'])
            try:
                if id_usuario:
                    execute_query(
                        'UPDATE usuarios SET nome = %s, email = %s, celular = %s, '
                        'data_nascimento = %s, cpf = %s, nivel_acesso = %s, cep = %s, '
                        'endereco = %s, numero = %s, complemento = %s, cidade = %s '
                        'WHERE id_usuario = %s',
                        dados + (id_usuario,))
                    flash('Usuário atualizado.', 'success')
                else:
                    execute_insert(
                        'INSERT INTO usuarios (nome, email, celular, data_nascimento, cpf, '
                        'nivel_acesso, cep, endereco, numero, complemento, cidade) '
                        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                        dados)
                    flash('Usuário cadastrado.', 'success')
                return redirect(url_for('lista_usuarios'))
            except Error as erro:
                # 1062: e-mail ou CPF já cadastrado (UNIQUE no banco)
                if erro.errno == 1062:
                    erros.append('Já existe um usuário com esse e-mail ou CPF.')
                else:
                    raise

    return render_template('usuario_form.html', usuario=usuario, erros=erros)


@app.route('/usuarios/<int:id_usuario>/excluir', methods=['POST'])
def excluir_usuario(id_usuario):
    execute_query('DELETE FROM usuarios WHERE id_usuario = %s', (id_usuario,))
    flash('Usuário excluído.', 'success')
    return redirect(url_for('lista_usuarios'))


# PETS

@app.route('/pets')
def lista_pets():
    pets = execute_query('SELECT * FROM pets ORDER BY nome', fetch=True)
    return render_template('pet_lista.html', pets=pets)


@app.route('/pets/cadastro', methods=['GET', 'POST'])
@app.route('/pets/<int:id_pet>/editar', methods=['GET', 'POST'])
def cadastro_pet(id_pet=None):
    pet = {}
    erros = []

    if id_pet:
        pet = execute_one('SELECT * FROM pets WHERE id_pet = %s', (id_pet,))
        if pet is None:
            abort(404)

    if request.method == 'POST':
        pet.update({
            'nome': request.form.get('nome', '').strip(),
            'especie': request.form.get('especie', ''),
            'raca': request.form.get('raca', '').strip() or None,
            'porte': request.form.get('porte', '') or None,
            'data_nascimento': request.form.get('data_nascimento', '').strip() or None,
            # Aceita 32,5 ou 32.5: o banco usa ponto
            'peso': request.form.get('peso', '').strip().replace(',', '.') or None,
            'tutor': request.form.get('tutor', '').strip(),
            'observacoes': request.form.get('observacoes', '').strip() or None,
        })

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

        if not erros:
            dados = (pet['nome'], pet['especie'], pet['raca'], pet['porte'],
                     pet['data_nascimento'], pet['peso'], pet['tutor'], pet['observacoes'])
            if id_pet:
                execute_query(
                    'UPDATE pets SET nome = %s, especie = %s, raca = %s, porte = %s, '
                    'data_nascimento = %s, peso = %s, tutor = %s, observacoes = %s '
                    'WHERE id_pet = %s',
                    dados + (id_pet,))
                flash('Pet atualizado.', 'success')
            else:
                execute_insert(
                    'INSERT INTO pets (nome, especie, raca, porte, data_nascimento, peso, '
                    'tutor, observacoes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                    dados)
                flash('Pet cadastrado.', 'success')
            return redirect(url_for('lista_pets'))

    return render_template('pet_form.html', pet=pet, erros=erros)


@app.route('/pets/<int:id_pet>/excluir', methods=['POST'])
def excluir_pet(id_pet):
    execute_query('DELETE FROM pets WHERE id_pet = %s', (id_pet,))
    flash('Pet excluído.', 'success')
    return redirect(url_for('lista_pets'))


# SERVIÇOS

@app.route('/servicos')
def lista_servicos():
    servicos = execute_query('SELECT * FROM servicos ORDER BY nome', fetch=True)
    return render_template('servico_lista.html', servicos=servicos)


@app.route('/servicos/cadastro', methods=['GET', 'POST'])
@app.route('/servicos/<int:id_servico>/editar', methods=['GET', 'POST'])
def cadastro_servico(id_servico=None):
    servico = {'ativo': 1}
    erros = []

    if id_servico:
        servico = execute_one('SELECT * FROM servicos WHERE id_servico = %s', (id_servico,))
        if servico is None:
            abort(404)

    if request.method == 'POST':
        servico.update({
            'nome': request.form.get('nome', '').strip(),
            'descricao': request.form.get('descricao', '').strip() or None,
            'preco': request.form.get('preco', '').strip().replace(',', '.'),
            'duracao_minutos': request.form.get('duracao_minutos', '').strip(),
            # Checkbox desmarcado não é enviado (aula 4)
            'ativo': 1 if request.form.get('ativo') else 0,
        })

        if not servico['nome']:
            erros.append('O nome do serviço é obrigatório.')
        try:
            float(servico['preco'])
        except ValueError:
            erros.append('Digite um preço válido.')
        if not servico['duracao_minutos'].isdigit():
            erros.append('A duração deve ser um número de minutos.')

        if not erros:
            dados = (servico['nome'], servico['descricao'], servico['preco'],
                     servico['duracao_minutos'], servico['ativo'])
            if id_servico:
                execute_query(
                    'UPDATE servicos SET nome = %s, descricao = %s, preco = %s, '
                    'duracao_minutos = %s, ativo = %s WHERE id_servico = %s',
                    dados + (id_servico,))
                flash('Serviço atualizado.', 'success')
            else:
                execute_insert(
                    'INSERT INTO servicos (nome, descricao, preco, duracao_minutos, ativo) '
                    'VALUES (%s, %s, %s, %s, %s)',
                    dados)
                flash('Serviço cadastrado.', 'success')
            return redirect(url_for('lista_servicos'))

    return render_template('servico_form.html', servico=servico, erros=erros)


@app.route('/servicos/<int:id_servico>/excluir', methods=['POST'])
def excluir_servico(id_servico):
    execute_query('DELETE FROM servicos WHERE id_servico = %s', (id_servico,))
    flash('Serviço excluído.', 'success')
    return redirect(url_for('lista_servicos'))


if __name__ == '__main__':
    app.run(debug = True)
