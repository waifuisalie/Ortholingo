# Revisão do conteúdo à luz do *Missal Bizantino* — 31/07/2026

Revisão de todo o conteúdo do Ortholingo (58 frases, 8 unidades) contra
`sources/Divina-liturgia-explicada-e-meditada.pdf` — *A Divina Liturgia de São
João Crisóstomo, Explicada e Meditada*, Mons. Pedro Arbex, ed. Pe. André
Sperandio (Pequeno Missal Bizantino, 2015).

---

## ⚠ Antes de tudo: duas ressalvas sobre a fonte

**1. O arquivo novo não chegou.** O PDF mais recente em `sources/` é de
**25/07**, adicionado na sessão anterior. Nenhum arquivo novo apareceu. Como o
nome («explicada e meditada») bate exatamente com a descrição, esta revisão foi
feita contra ele. **Se você tinha outro PDF em mente, ele não salvou** — e esta
revisão foi feita contra o documento errado.

**2. É um missal bizantino CATÓLICO, não ortodoxo.** O vocabulário denuncia:
«Missa», «Monsenhor», «Assembléia». Isso importa para um app de catecúmenos
ortodoxos:

- ✅ **O texto litúrgico está limpo.** O Credo é apresentado **sem o
  *filioque***, e o missal explica com precisão por quê (p. ~48): «enquanto os
  latinos juntaram-lhe […] o inciso "Filioque"[…], que nenhum texto grego
  continha, os Orientais conservaram-no como os concílios o haviam promulgado».
- ⚠ **O comentário tem viés.** Na mesma página, resume a fé oriental como «que
  o Espírito Santo procede do Pai **pelo** Filho» — a fórmula *per Filium*, que
  é leitura greco-católica, não a formulação ortodoxa corrente.

**Consequência prática:** esta fonte é **forte para descobrir lacunas** (o
sumário dela é a Liturgia em ordem) e **fraca para corrigir traduções** — as
nossas vêm do Devocional ortodoxo e do texto GOA. Nada foi reescrito. As
divergências abaixo são **para você e o padre decidirem**, não correções.

---

## 1. A lacuna que você perguntou: a Litania das Súplicas ✅ RESOLVIDA

**Estava faltando — era a lacuna mais séria do app. Foi construída em 31/07.**

Adicionadas a `unit5-grande-entrada`, **antes** de `paraschu-kyrie`:

| id | grego | duração |
|---|---|---|
| `plirosomen` | Πληρώσωμεν τὴν δέησιν ἡμῶν τῷ Κυρίῳ. | 2,5s · inteira |
| `angelon-irinis` | Ἄγγελον εἰρήνης, πιστὸν ὁδηγόν, φύλακα τῶν ψυχῶν καὶ τῶν σωμάτων ἡμῶν παρὰ τοῦ Κυρίου αἰτησώμεθα. | 6,3s · 3 partes |

A divisão das lições caiu bem: **Lição 2 = `angelon-irinis` + `paraschu-kyrie`**
— a petição e a sua resposta lado a lado. **Não há mais respostas órfãs no app.**

O `context_pt` de `plirosomen` ensina uma sutileza que só se vê ouvindo: a
*primeira* petição desta litania ainda se responde «Κύριε, ἐλέησον»; só a
partir da segunda é que muda para «Παράσχου, Κύριε».

*O registro original da lacuna segue abaixo.*

O que você chamou de «intercessão da paz» é a **Litania das Súplicas**
(Τὰ Πληρωτικά; o missal a chama de **«éticis»**, de αἰτήσεις, «pedidos»).
O missal a descreve assim:

> «pedidos chamada "éticis", rogam-se a Deus graças úteis a todos e a cada um
> dos presentes no templo: um dia pacífico e santo; **um anjo de paz** que nos
> acompanhe durante o dia e nos guie no caminho da salvação; o perdão de nossos
> pecados […]»

**O defeito concreto:** o app ensina `paraschu-kyrie` («Concede, Senhor») — mas
**nenhuma das petições que essa resposta responde existe**. O catecúmeno aprende
uma resposta sem pergunta.

Verifiquei isso em todo o app: **`paraschu-kyrie` é a ÚNICA resposta órfã.**
Todas as outras têm o seu chamado presente (`si-kyrie`←`tis-panagias`,
`ke-to-pnevmati-su`←`irini-pasi`, `anafora-ke-meta`←`anafora-haris`,
`anafora-echomen`←`anafora-ano`, `anafora-axion`←`anafora-efcharistisomen`).

Texto grego (GOA, confirmado):

| Grego | Português |
|---|---|
| Πληρώσωμεν τὴν δέησιν ἡμῶν τῷ Κυρίῳ. | Completemos a nossa oração ao Senhor. |
| Τὴν ἡμέραν πᾶσαν τελείαν, ἁγίαν, εἰρηνικὴν καὶ ἀναμάρτητον παρὰ τοῦ Κυρίου αἰτησώμεθα. | Que todo o dia seja perfeito, santo, pacífico e sem pecado, peçamos ao Senhor. |
| **Ἄγγελον εἰρήνης, πιστὸν ὁδηγόν, φύλακα τῶν ψυχῶν καὶ τῶν σωμάτων ἡμῶν παρὰ τοῦ Κυρίου αἰτησώμεθα.** | **Um anjo de paz, guia fiel, guardião das nossas almas e dos nossos corpos, peçamos ao Senhor.** |
| Συγγνώμην καὶ ἄφεσιν τῶν ἁμαρτιῶν καὶ τῶν πλημμελημάτων ἡμῶν παρὰ τοῦ Κυρίου αἰτησώμεθα. | Perdão e remissão dos nossos pecados e transgressões, peçamos ao Senhor. |

Todas respondidas com «Παράσχου, Κύριε».

---

## 2. Outras lacunas de cobertura

Diferença entre o sumário do missal (que é a Liturgia em ordem) e as nossas 58 frases.

### Alta prioridade — são partes DO POVO, ditas em voz alta

| Falta | Grego | Por que importa |
|---|---|---|
| **Ósculo da paz** | Ἀγαπήσωμεν ἀλλήλους, ἵνα ἐν ὁμονοίᾳ ὁμολογήσωμεν → **Πατέρα, Υἱὸν καὶ ἅγιον Πνεῦμα, Τριάδα ὁμοούσιον καὶ ἀχώριστον** | O povo **completa a frase do sacerdote**. O missal dá destaque (p. 45). Vem logo antes do Credo — que já temos inteiro. |
| **Litania das Súplicas** | ver §1 | resolve a resposta órfã |
| **Oração pré-comunhão** | Τοῦ δείπνου σου τοῦ μυστικοῦ σήμερον, Υἱὲ Θεοῦ, κοινωνόν με παράλαβε… | **Rezada por todo comungante**, em voz alta. É a oração que o catecúmeno mais vai querer saber quando finalmente comungar. |
| **Inclinação das cabeças** | Τὰς κεφαλὰς ἡμῶν τῷ Κυρίῳ κλίνωμεν → Σοί, Κύριε | Já temos `si-kyrie`, mas só ligado a `tis-panagias`. Este é o **segundo** contexto dele. |

### Média prioridade

| Falta | Observação |
|---|---|
| **Dípticos** — Καὶ ὧν ἕκαστος κατὰ διάνοιαν ἔχει καὶ πάντων καὶ πασῶν | resposta: Κύριε ἐλέησον (já temos) |
| **Ectenia / Súplica Insistente** (Ἐκτενής) | o missal dedica seção (p. 37); respostas são «Κύριε ἐλέησον» ×3 |
| **Despedida dos catecúmenos** | tematicamente central para um app de catecúmenos — hoje ausente por completo |
| **Substituição do Triságion** — Ὅσοι εἰς Χριστὸν ἐβαπτίσθητε | usado na Páscoa, Natal, Teofania |

### Fora de escopo (corretamente ausentes)

Tropário/Kontákion (variam por dia — quebram o corpus fechado), orações
sacerdotais em voz baixa (χαμηλοφώνως), Prótese, zeón, antídoron (ritos sem
texto do povo).

---

## 3. Divergências de tradução — NÃO corrigidas, para decisão

Nossas traduções vêm do Devocional (ortodoxo) e do GOA. O missal às vezes
difere. **Nenhuma foi alterada.** Em quase todos os casos eu manteria a nossa.

| Item | Nossa (Devocional) | Missal Arbex | Comentário |
|---|---|---|---|
| `credo-1` | Pai **onipotente** | Pai **todo-poderoso** | ambas para Παντοκράτορα. «Todo-poderoso» é mais comum no uso litúrgico em PT; «onipotente» é mais latinizante. **Vale perguntar ao padre.** |
| `meta-fovou` | fé e **amor** | fé e **caridade** | ἀγάπης. «Caridade» é o registro tradicional; «amor» é mais direto para um iniciante. Manteria a nossa. |
| `anafora-lavete` | que por vós é **partido** | dado por vós | o grego é κλώμενον = «partido». **A nossa está mais literal.** |
| `anafora-piete` | o **da nova aliança** | o sangue da Nova Aliança | idem — a nossa segue o grego (τὸ τῆς καινῆς διαθήκης). |

### Confirmações (o missal bate com o que temos)

`evlogimeni-i-vasilia` («Bendito seja o reino do Pai…»), `trisagion`
(«Santo Deus, Santo Forte…»), `anafora-axion` («É digno e justo»),
`en-irini` («em paz, oremos ao Senhor»), `sofia-orthi` («A Sabedoria!»),
`credo-12` («e a vida do mundo que há de vir»).

**Nenhum erro de tradução foi encontrado.** As divergências acima são escolhas
de registro, não erros.

---

## 3b. Procedência do que está no app — leitura honesta

Nem tudo no app vem de uma fonte. Convém ter isso claro antes da revisão do padre:

| O quê | Quanto | De onde vem |
|---|---|---|
| Tradução corrida (`pt`) de cada frase | 58 | **das fontes** — cada item cita Devocional / GOA no campo `source:` |
| **Glosas por palavra (`words[].pt`)** | **699 palavras** | **escritas por mim** (31/07). Nenhuma fonte faz grego→português palavra a palavra |
| **Títulos (`title`)** | **25** | **inventados por mim** (31/07) |

As glosas por palavra são uma *decomposição* da tradução aprovada na ordem do
grego — método defensável, e é exatamente por isso que tudo carrega
`review: pending`. Mas **não são material de fonte**, e hoje são o maior corpo
de texto não revisado do app.

Além disso: das 58 traduções corridas, **13 foram conferidas** contra o missal
(bateram, várias literalmente). As outras 45 não foram contraditadas — apenas
não foram cotejadas, porque o missal é comentário e não cita todas as linhas.

---

## 4. Correção já aplicada: o mapa da Liturgia

`content/liturgy-map.yaml` tinha dois defeitos, ambos corrigidos:

1. **`paraschu-kyrie` estava na seção `enarxis`** — errado. A Grande Litania de
   abertura é respondida com «Κύριε, ἐλέησον», não «Παράσχου, Κύριε». Verifiquei
   por posição no texto GOA: Grande Litania (l. 84) → Querubikon (l. 667) →
   Πληρωτικά (l. 726) → **primeiro «Παράσχου, Κύριε» (l. 759)**. Ele nunca ocorre
   na enarxis. Movido para a nova seção **Litania das Súplicas**, depois da
   Grande Entrada. (A unidade `unit5-grande-entrada` já estava certa.)
2. **Zero itens marcados `future`** — o mapa afirmava cobertura total da
   Liturgia, o que é falso. Agora há 7 itens `future`, todos com o grego
   **copiado literalmente** do texto GOA.

Efeito: o medidor da página `/liturgia` agora tem **teto de 90%**, não 100% —
o app passa a admitir o que ainda lhe falta.

**Duas lacunas foram deixadas FORA do mapa de propósito:** a Ectenia (Ἐκτενής)
e a despedida dos catecúmenos. O texto GOA em `sources/` é de uma liturgia
dominical e **não as contém** — o grego teria de ser inventado, e texto
litúrgico aqui nunca é inventado. Estão registradas em comentário no topo do
mapa, à espera de uma fonte que as traga.

## 5. Recomendação

1. ~~Preencher a Litania das Súplicas~~ ✅ **feito em 31/07** (ver §1)
2. **Ósculo da paz** — pequeno (2 frases), alto valor: o povo completa a frase
   do sacerdote, e encaixa exatamente antes do Credo que já existe. É o
   próximo candidato óbvio.
3. **Oração pré-comunhão** — a que o catecúmeno mais vai querer.
4. **Inclinação das cabeças** e os **Dípticos** — pequenos, reaproveitam
   respostas que já existem (`si-kyrie`, `kyrie-eleison`).
5. Conseguir uma fonte que contenha a **Ectenia** e a **despedida dos
   catecúmenos** — o texto GOA em `sources/` é dominical e não as traz.
6. Levar as 4 divergências de tradução à revisão do padre, junto com as **699
   glosas por palavra e os 25 títulos** (ver §3b — nada disso vem de fonte).

**Estado do mapa:** o medidor de `/liturgia` tem hoje teto de **94%**
(era 90% antes da Litania das Súplicas; 100% falso antes da revisão).
Restam 5 itens `future`.
