from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Listas de dicionários simulando as tabelas (como a lista de produtos da aula 3).
# Ficam na memória: o que for cadastrado some ao reiniciar o servidor.
usuarios = [
    {'id': 1, 'nome': 'Usuário 1', 'email': 'user1@example.com',
     'celular': '1234567890', 'nivel_acesso': 'Usuário'},
    {'id': 2, 'nome': 'Usuário 2', 'email': 'user2@example.com',
     'celular': '9876543210', 'nivel_acesso': 'Administrador'},
]

pets = [
    {'id': 1, 'nome': 'Thor', 'especie': 'Cão', 'raca': 'Golden Retriever',
     'porte': 'Grande', 'peso': '32,5', 'tutor': 'Ana Souza'},
    {'id': 2, 'nome': 'Mimi', 'especie': 'Gato', 'raca': 'Siamês',
     'porte': 'Pequeno', 'peso': '4,2', 'tutor': 'Carlos Lima'},
]

servicos = [
    {'id': 1, 'nome': 'Banho', 'preco': '50,00', 'duracao_minutos': '40', 'ativo': 'sim'},
    {'id': 2, 'nome': 'Tosa higiênica', 'preco': '40,00', 'duracao_minutos': '30', 'ativo': 'sim'},
    {'id': 3, 'nome': 'Consulta veterinária', 'preco': '150,00', 'duracao_minutos': '30', 'ativo': 'nao'},
]


# LOGIN E PAINEL

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

        # Sem erros: segue para o painel (a autenticação de verdade fica para as próximas aulas)
        if not erros:
            return redirect(url_for('dashboard'))

    return render_template('login.html', email=email, erros=erros)


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html',
                           total_usuarios=len(usuarios),
                           total_pets=len(pets),
                           total_servicos=len(servicos))


# BUSCA (campo "Procurar" do menu)

@app.route('/busca')
def busca():
    termo = request.args.get('q', '').strip()
    achados_usuarios = []
    achados_pets = []
    achados_servicos = []

    if termo:
        achados_usuarios = [u for u in usuarios if termo.lower() in u['nome'].lower()]
        achados_pets = [p for p in pets if termo.lower() in p['nome'].lower()]
        achados_servicos = [s for s in servicos if termo.lower() in s['nome'].lower()]

    return render_template('busca.html', termo=termo, usuarios=achados_usuarios,
                           pets=achados_pets, servicos=achados_servicos)


# USUÁRIOS

@app.route('/usuarios')
def lista_usuarios():
    return render_template('usuario_lista.html', usuarios=usuarios)


@app.route('/usuarios/cadastro', methods=['GET', 'POST'])
def cadastro_usuario():
    usuario = {}
    erros = []

    if request.method == 'POST':
        usuario = {
            'id': len(usuarios) + 1,
            'nome': request.form.get('nome', '').strip(),
            'email': request.form.get('email', '').strip(),
            'celular': request.form.get('celular', '').strip(),
            'data_nascimento': request.form.get('data_nascimento', '').strip(),
            'cpf': request.form.get('cpf', '').strip(),
            'nivel_acesso': request.form.get('nivel_acesso', ''),
            'cep': request.form.get('cep', '').strip(),
            'endereco': request.form.get('endereco', '').strip(),
            'numero': request.form.get('numero', '').strip(),
            'complemento': request.form.get('complemento', '').strip(),
            'cidade': request.form.get('cidade', '').strip(),
        }

        if len(usuario['nome']) < 3:
            erros.append('O nome deve ter pelo menos 3 caracteres.')
        if '@' not in usuario['email']:
            erros.append('Digite um e-mail válido.')
        if not usuario['nivel_acesso']:
            erros.append('Escolha o nível de acesso.')

        if not erros:
            usuarios.append(usuario)
            return redirect(url_for('lista_usuarios'))

    return render_template('usuario_form.html', usuario=usuario, erros=erros)


# PETS

@app.route('/pets')
def lista_pets():
    return render_template('pet_lista.html', pets=pets)


@app.route('/pets/cadastro', methods=['GET', 'POST'])
def cadastro_pet():
    pet = {}
    erros = []

    if request.method == 'POST':
        pet = {
            'id': len(pets) + 1,
            'nome': request.form.get('nome', '').strip(),
            'especie': request.form.get('especie', ''),
            'raca': request.form.get('raca', '').strip(),
            'porte': request.form.get('porte', ''),
            'data_nascimento': request.form.get('data_nascimento', '').strip(),
            'peso': request.form.get('peso', '').strip(),
            'tutor': request.form.get('tutor', '').strip(),
            'observacoes': request.form.get('observacoes', '').strip(),
        }

        if not pet['nome']:
            erros.append('O nome do pet é obrigatório.')
        if not pet['especie']:
            erros.append('Escolha a espécie.')
        if not pet['tutor']:
            erros.append('O nome do tutor é obrigatório.')

        if not erros:
            pets.append(pet)
            return redirect(url_for('lista_pets'))

    return render_template('pet_form.html', pet=pet, erros=erros)


# SERVIÇOS

@app.route('/servicos')
def lista_servicos():
    return render_template('servico_lista.html', servicos=servicos)


@app.route('/servicos/cadastro', methods=['GET', 'POST'])
def cadastro_servico():
    servico = {'ativo': 'sim'}
    erros = []

    if request.method == 'POST':
        servico = {
            'id': len(servicos) + 1,
            'nome': request.form.get('nome', '').strip(),
            'descricao': request.form.get('descricao', '').strip(),
            'preco': request.form.get('preco', '').strip(),
            'duracao_minutos': request.form.get('duracao_minutos', '').strip(),
            # Checkbox desmarcado não é enviado: .get() com valor padrão 'nao' (aula 4)
            'ativo': request.form.get('ativo', 'nao'),
        }

        if not servico['nome']:
            erros.append('O nome do serviço é obrigatório.')
        if not servico['preco']:
            erros.append('O preço é obrigatório.')
        if not servico['duracao_minutos']:
            erros.append('A duração é obrigatória.')

        if not erros:
            servicos.append(servico)
            return redirect(url_for('lista_servicos'))

    return render_template('servico_form.html', servico=servico, erros=erros)


if __name__ == '__main__':
    app.run(debug = True)
