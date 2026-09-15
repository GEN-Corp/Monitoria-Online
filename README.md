# 🎓 Monitoria Online

> Plataforma para gerenciamento e organização de monitorias acadêmicas.

**Instituto Federal de Educação, Ciência e Tecnologia de São Paulo — IFSP**
**Curso:** Técnico em Informática
**Disciplina:** Aula 01 — Sprint 0
**Etapa:** Descoberta e Planejamento do Levantamento de Requisitos

---

## 👥 Integrantes

* **Gabriel Rodrigues da Rocha Forti**
* **Eduardo Gritti Medeiros Teixeira**
* **Nicolas de Azevedo Andrade Santana**

---

# 📚 Sobre o Projeto

A **Monitoria Online** é uma plataforma desenvolvida com o objetivo de centralizar e organizar o processo de monitoria acadêmica.

A monitoria é uma importante ferramenta de apoio ao aprendizado, permitindo que estudantes esclareçam dúvidas e aprofundem seus conhecimentos com o auxílio de monitores e professores.

Entretanto, em muitas instituições, esse processo ainda ocorre de maneira descentralizada, utilizando aplicativos de mensagens, e-mails ou atendimentos presenciais. Isso pode dificultar:

* A organização das solicitações;
* O agendamento dos atendimentos;
* O acompanhamento das monitorias;
* O controle de frequência;
* O registro das dúvidas;
* O acompanhamento do desempenho dos monitores;
* A geração de relatórios.

A proposta do projeto é disponibilizar um **ambiente centralizado**, permitindo que alunos, monitores, professores e coordenadores acompanhem as diferentes etapas do processo de monitoria em um único sistema.

---

# 🎯 Objetivo

Desenvolver uma plataforma capaz de facilitar a comunicação entre **alunos, monitores e professores**, organizando o processo de monitoria acadêmica.

O sistema deverá permitir:

* Agendamento de atendimentos;
* Registro e acompanhamento de dúvidas;
* Organização das monitorias;
* Controle de frequência;
* Avaliação dos atendimentos;
* Gerenciamento de usuários;
* Acompanhamento das atividades;
* Geração de relatórios;
* Visualização de indicadores por meio de dashboards.

---

# ❗ Problema a ser resolvido

Atualmente, estudantes podem encontrar dificuldades para localizar monitores disponíveis e solicitar auxílio em determinadas disciplinas.

Além disso, quando o processo é realizado manualmente, podem surgir problemas relacionados a:

* Falta de organização dos horários;
* Dificuldade no controle de vagas;
* Falta de histórico dos atendimentos;
* Ausência de controle centralizado de frequência;
* Dificuldade para acompanhar as dúvidas dos alunos;
* Pouca visibilidade dos professores sobre as monitorias;
* Dificuldade para avaliar o desempenho dos monitores;
* Falta de indicadores para auxiliar a gestão acadêmica.

A **Monitoria Online** busca solucionar essas dificuldades por meio de um sistema centralizado de gerenciamento.

---

# 👤 Público-alvo

O sistema será destinado principalmente aos seguintes usuários:

| Perfil              | Descrição                                                                               |
| ------------------- | --------------------------------------------------------------------------------------- |
| 🎓 **Aluno**        | Solicita monitorias, registra dúvidas, participa dos atendimentos e realiza avaliações. |
| 👨‍💻 **Monitor**   | Realiza atendimentos, responde dúvidas e acompanha suas atividades.                     |
| 👨‍🏫 **Professor** | Acompanha monitorias, alunos, desempenho e relatórios.                                  |
| 🏫 **Coordenador**  | Gerencia informações e acompanha indicadores gerais das monitorias.                     |
| 🏢 **Instituição**  | Utiliza a plataforma para centralizar e organizar o processo de monitoria.              |

---

# ⚙️ Funcionalidades Previstas

## 👥 1. Gerenciamento de Usuários — CRUD

O sistema deverá possuir gerenciamento completo dos usuários.

### 🎓 Alunos

* [ ] Cadastrar aluno
* [ ] Consultar aluno
* [ ] Atualizar cadastro
* [ ] Excluir cadastro

### 👨‍🏫 Professores

* [ ] Cadastrar professor
* [ ] Consultar professor
* [ ] Atualizar cadastro
* [ ] Excluir cadastro

### 👨‍💻 Monitores

* [ ] Cadastrar monitor
* [ ] Consultar monitor
* [ ] Atualizar cadastro
* [ ] Excluir cadastro

### 🔐 Autenticação

* [ ] Login
* [ ] Autenticação
* [ ] Recuperação de senha
* [ ] Controle de permissões por perfil

---

# 📖 2. Gerenciamento de Disciplinas — CRUD

O sistema deverá permitir o gerenciamento das disciplinas oferecidas pela instituição.

* [ ] Cadastrar disciplina
* [ ] Consultar disciplina
* [ ] Editar disciplina
* [ ] Excluir disciplina

---

# 🗓️ 3. Organização das Monitorias — CRUD

Será possível administrar as monitorias e seus respectivos atendimentos.

* [ ] Cadastrar monitoria
* [ ] Consultar monitorias
* [ ] Atualizar monitoria
* [ ] Cancelar monitoria
* [ ] Definir monitor responsável
* [ ] Associar monitor à disciplina
* [ ] Agendar monitorias individuais
* [ ] Agendar monitorias em grupo
* [ ] Controle automático de vagas
* [ ] Histórico das monitorias

---

# 💬 4. Atendimento de Dúvidas — CRUD

O sistema contará com um sistema de tickets para organização das dúvidas dos estudantes.

### Funcionalidades

* [ ] Abrir ticket
* [ ] Consultar ticket
* [ ] Editar ticket
* [ ] Encerrar ticket
* [ ] Responder dúvidas
* [ ] Encaminhar dúvidas para outro monitor
* [ ] Visualizar histórico completo do atendimento

### 📌 Status do atendimento

```text
Aberta
   ↓
Em atendimento
   ↓
Respondida
   ↓
Encerrada
```

---

# 📝 5. Frequência — CRUD

O sistema deverá permitir o controle da participação dos alunos nas monitorias.

* [ ] Registrar presença
* [ ] Consultar presença
* [ ] Alterar presença
* [ ] Excluir registro quando autorizado
* [ ] Consultar histórico de participação

---

# ⭐ 6. Avaliações — CRUD

Após um atendimento, o aluno poderá avaliar a monitoria realizada.

* [ ] Registrar avaliação
* [ ] Consultar avaliação
* [ ] Alterar avaliação
* [ ] Excluir avaliação
* [ ] Adicionar comentários

As avaliações poderão ser utilizadas posteriormente para gerar indicadores de qualidade e desempenho.

---

# 📊 7. Relatórios e Dashboard

A plataforma deverá disponibilizar ferramentas para acompanhamento das atividades.

### Dashboard dos Monitores

* Quantidade de atendimentos;
* Dúvidas respondidas;
* Monitorias realizadas;
* Avaliações recebidas.

### Dashboard dos Professores

* Monitorias realizadas;
* Participação dos alunos;
* Dúvidas por disciplina;
* Frequência;
* Indicadores de desempenho.

### Relatórios

* [ ] Relatório de monitorias
* [ ] Relatório de frequência
* [ ] Relatório de desempenho
* [ ] Quantidade de dúvidas por disciplina
* [ ] Indicadores de utilização do sistema
* [ ] Exportação dos relatórios

---

# 👥 Stakeholders

O levantamento de requisitos será realizado com pessoas que participam diretamente do processo de monitoria acadêmica.

Os principais stakeholders são:

* 🎓 Estudantes;
* 👨‍💻 Monitores;
* 👨‍🏫 Professores;
* 🏫 Coordenadores de curso;
* 📚 Responsáveis pela gestão acadêmica.

### 🔒 Privacidade

Durante as entrevistas, os participantes serão identificados apenas por seu **perfil**, evitando a coleta de dados pessoais desnecessários.

Exemplos:

> "Aluno do Ensino Superior"

> "Monitor da disciplina de Programação"

> "Professor da área de Computação"

Essa abordagem busca preservar a privacidade dos participantes durante o levantamento de requisitos.

---

# 🔎 Estratégia de Levantamento de Requisitos

O levantamento de requisitos será realizado utilizando **entrevistas semiestruturadas**.

Essa abordagem permite que os entrevistados respondam às perguntas previamente elaboradas e, ao mesmo tempo, apresentem novas ideias, necessidades e problemas identificados durante a conversa.

## 📋 Etapas

```text
1. Identificação dos stakeholders
              ↓
2. Elaboração do roteiro
              ↓
3. Definição dos participantes
              ↓
4. Agendamento das entrevistas
              ↓
5. Realização das entrevistas
              ↓
6. Registro das respostas
              ↓
7. Consolidação das informações
              ↓
8. Identificação dos requisitos
              ↓
9. Identificação das regras de negócio
              ↓
10. Validação com os entrevistados
              ↓
11. Criação das histórias de usuário
              ↓
12. Elaboração do backlog inicial
              ↓
13. Priorização com o Product Owner
```

---

# 📌 Sprint 0

A **Sprint 0** tem como objetivo preparar a base do projeto antes do início do desenvolvimento.

Nesta etapa serão realizados:

* Levantamento inicial do problema;
* Identificação dos stakeholders;
* Definição do público-alvo;
* Levantamento de requisitos;
* Entrevistas;
* Identificação de requisitos funcionais;
* Identificação de requisitos não funcionais;
* Identificação das regras de negócio;
* Criação das histórias de usuário;
* Construção do backlog inicial;
* Priorização das funcionalidades.

---

# 📋 Requisitos

A partir das entrevistas e do levantamento realizado, os requisitos serão classificados em diferentes categorias.

### Requisitos Funcionais

Representam as funcionalidades que o sistema deverá oferecer.

Exemplos:

* Cadastro de usuários;
* Agendamento de monitorias;
* Criação de tickets;
* Registro de presença;
* Avaliação de atendimentos;
* Geração de relatórios.

### Requisitos Não Funcionais

Representam características relacionadas à qualidade e ao funcionamento do sistema.

Exemplos:

* Segurança;
* Disponibilidade;
* Usabilidade;
* Desempenho;
* Controle de acesso;
* Privacidade dos dados.

### Regras de Negócio

Representam regras que deverão ser respeitadas pelo sistema.

Exemplos:

* Apenas usuários autorizados poderão acessar determinadas funcionalidades;
* O número de vagas de uma monitoria deverá ser controlado;
* Apenas participantes autorizados poderão alterar determinados registros;
* Cada atendimento deverá possuir um status;
* O acesso às informações deverá respeitar o perfil do usuário.

---

# 📖 Histórias de Usuário

Após o levantamento dos requisitos, as funcionalidades serão transformadas em histórias de usuário.

O formato utilizado será:

> **Como** [tipo de usuário],
> **quero** [ação/funcionalidade],
> **para** [objetivo/benefício].

### Exemplo

> Como **aluno**, quero **agendar uma monitoria**, para **conseguir auxílio em uma disciplina na qual estou com dificuldades**.

---

# 🗂️ Backlog Inicial

O backlog será construído a partir das necessidades identificadas durante as entrevistas.

As funcionalidades serão posteriormente:

1. Documentadas;
2. Transformadas em histórias de usuário;
3. Estimadas;
4. Priorizadas;
5. Distribuídas nas Sprints.

A priorização será realizada em conjunto com o **Product Owner**.

---

# 🚀 Roadmap Inicial

```text
SPRINT 0
│
├── Descoberta
├── Levantamento de requisitos
├── Stakeholders
├── Entrevistas
└── Backlog inicial
        │
        ▼
SPRINT 1
│
├── Estrutura inicial do sistema
├── Autenticação
└── Gerenciamento de usuários
        │
        ▼
SPRINT 2
│
├── Disciplinas
├── Monitores
└── Organização das monitorias
        │
        ▼
SPRINT 3
│
├── Tickets
├── Atendimento de dúvidas
└── Histórico
        │
        ▼
SPRINT 4
│
├── Frequência
├── Avaliações
└── Relatórios
        │
        ▼
SPRINT 5
│
├── Dashboards
├── Melhorias
└── Testes e validação
```

> *O roadmap apresentado é inicial e poderá ser alterado conforme os resultados do levantamento de requisitos e a priorização do backlog.*

---

# 🏗️ Estrutura Conceitual do Sistema

A plataforma será organizada de acordo com os principais componentes do processo de monitoria:

```text
                    ┌─────────────────┐
                    │  Monitoria      │
                    │     Online      │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
    ┌───────────┐      ┌────────────┐     ┌─────────────┐
    │ Usuários  │      │ Monitorias │     │ Disciplinas │
    └───────────┘      └────────────┘     └─────────────┘
          │                  │
          │                  ▼
          │           ┌──────────────┐
          │           │ Atendimento  │
          │           │   de dúvidas │
          │           └──────┬───────┘
          │                  │
          ├──────────────────┼─────────────────┐
          ▼                  ▼                 ▼
    ┌───────────┐      ┌────────────┐    ┌────────────┐
    │ Frequência│      │ Avaliações │    │ Relatórios │
    └───────────┘      └────────────┘    └────────────┘
```

---

# 🎓 Instituição

**Instituto Federal de Educação, Ciência e Tecnologia de São Paulo — IFSP**

**Curso:** Engenharia de Software

**Projeto:** Monitoria Online

**Etapa:** Sprint 0 — Descoberta e Planejamento do Levantamento de Requisitos

---

## 👨‍💻 Equipe

| Integrante                         |
| ---------------------------------- |
| Gabriel Rodrigues da Rocha Forti   |
| Eduardo Gritti Medeiros Teixeira   |
| Nicolas de Azevedo Andrade Santana |

---

<p align="center">
  Desenvolvido como projeto acadêmico para o curso de <strong>Engenharia de Software — IFSP</strong>.
</p>

