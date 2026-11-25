-- DROP DATABASE IF EXISTS petfeliz;   -- tire o "--" só se quiser apagar tudo e recomeçar do zero

CREATE DATABASE IF NOT EXISTS petfeliz
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE petfeliz;

CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario      BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nome            VARCHAR(255) NOT NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    celular         VARCHAR(20),
    data_nascimento DATE,
    cpf             VARCHAR(14) UNIQUE,         -- gravado como 000.000.000-00
    nivel_acesso    VARCHAR(20) NOT NULL,       -- Usuário ou Administrador
    cep             VARCHAR(9),
    endereco        VARCHAR(255),
    numero          VARCHAR(20),
    complemento     VARCHAR(100),
    cidade          VARCHAR(100),
    criado_em       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em   TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

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
