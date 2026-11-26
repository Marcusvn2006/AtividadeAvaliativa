USE petfeliz;

-- perfis vem antes de usuarios, porque usuarios aponta para ele (chave estrangeira).
CREATE TABLE IF NOT EXISTS perfis (
    id_perfil     BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nome          VARCHAR(100) NOT NULL UNIQUE,
    descricao     VARCHAR(255),
    criado_em     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deletado_em   DATETIME NULL                         -- soft-delete (Capítulo 13.1)
);

CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario      BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nome            VARCHAR(255) NOT NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    senha           VARCHAR(255) NOT NULL,      -- guarda o HASH, nunca a senha
    celular         VARCHAR(20),
    data_nascimento DATE,
    cpf             VARCHAR(14) UNIQUE,         -- gravado como 000.000.000-00
    perfil_id       BIGINT UNSIGNED NOT NULL,
    cep             VARCHAR(9),
    endereco        VARCHAR(255),
    numero          VARCHAR(20),
    complemento     VARCHAR(100),
    cidade          VARCHAR(100),
    estado          CHAR(2),
    criado_em       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em   TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deletado_em     DATETIME NULL,                      -- soft-delete (Capítulo 13.1)
    CONSTRAINT fk_usuarios_perfis
        FOREIGN KEY (perfil_id) REFERENCES perfis (id_perfil)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

-- ============================================================
-- PARTE PRÓPRIA DO PET FELIZ
-- ============================================================

CREATE TABLE IF NOT EXISTS pets (
    id_pet          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nome            VARCHAR(100) NOT NULL,
    especie         VARCHAR(20) NOT NULL,       -- Cão, Gato, Ave, Roedor ou Outro
    raca            VARCHAR(100),
    porte           VARCHAR(20),                -- Pequeno, Médio ou Grande
    data_nascimento DATE,
    peso            DECIMAL(5,2),
    tutor           VARCHAR(255) NOT NULL,
    observacoes     TEXT,
    criado_em       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em   TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS servicos (
    id_servico      BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nome            VARCHAR(255) NOT NULL,
    descricao       TEXT,
    preco           DECIMAL(10,2) NOT NULL,
    duracao_minutos INT UNSIGNED NOT NULL,
    ativo           TINYINT(1) NOT NULL DEFAULT 1,
    criado_em       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em   TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- DADOS INICIAIS
-- Sem um usuário no banco ninguém consegue entrar no sistema (o login confere esta tabela).
-- O IGNORE pula a linha que já existe (nome e email são UNIQUE): importar de novo não duplica nada.
INSERT IGNORE INTO perfis (nome, descricao) VALUES
    ('Administrador', 'Acesso total ao sistema');

-- Usuário inicial: admin@petfeliz.com / senha Senha123 (gravada como hash, nunca a senha em texto puro)
INSERT IGNORE INTO usuarios (nome, email, senha, perfil_id) VALUES (
    'Administrador',
    'admin@petfeliz.com',
    'scrypt:32768:8:1$FPEXcV8lvNZZshsw$f8d37022605b70293fb3fbff06ff91a024351941dd40457857aa53698f209a11e8ae9b084e3536af5b8af9db6fc1042751d6c81b8833e03a3bc257004e98bcd6',
    (SELECT id_perfil FROM perfis WHERE nome = 'Administrador')
);
