CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    marca TEXT NOT NULL,
    modelo TEXT NOT NULL,
    tamanho TEXT,
    quantidade INTEGER NOT NULL,
    preco REAL NOT NULL,
    data_entrada TEXT NOT NULL,
    data_saida TEXT,
    data_cadastro TEXT NOT NULL
);