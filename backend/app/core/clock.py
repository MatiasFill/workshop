"""
`datetime.utcnow()` é depreciado desde o Python 3.12 (`DeprecationWarning`,
removido em versão futura). O substituto recomendado pela documentação é
`datetime.now(timezone.utc)` — mas isso retorna um datetime **aware**
(com timezone), e todas as colunas `DateTime` deste projeto são **naive**
(sem timezone, `sa.DateTime` sem `timezone=True`).

Trocar só as chamadas por `datetime.now(timezone.utc)` sem migrar as colunas
para `DateTime(timezone=True)` quebraria em runtime: comparar um datetime
aware com um naive vindo do banco levanta
`TypeError: can't compare offset-naive and offset-aware datetimes`.

`utcnow_naive()` faz a mesma coisa que `datetime.utcnow()` fazia (horário
atual em UTC, sem timezone anexado) sem usar a função depreciada — só
silencia o warning, não muda nenhum valor armazenado nem exige nova
migration. Se um dia o projeto migrar as colunas para timezone-aware, é
aqui que a troca acontece, num lugar só.
"""
from datetime import datetime, timezone


def utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
