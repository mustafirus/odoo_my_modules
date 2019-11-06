MAXIDX=8192
# MINVMID=3000
# MAXVMID=4000

def next_idx(cr, tab, col, min):
    cr.execute(_next_idx_sql.format(tab=tab, col=col, min=min))
    res = cr.fetchone()
    return res[0]


_next_idx_sql = '''
SELECT MIN({col}+1) FROM (
    SELECT {min} AS {col} UNION ALL
    SELECT
        MIN({col} + 1)
    FROM
        omixtory_{tab}) AS T1
WHERE
    {col}+1 NOT IN (SELECT {col} FROM omixtory_{tab}) 
'''



def calc_prefix(idx, base):
    n3 = int((idx - 1) / 254) + base
    n2 = (idx - 1) % 254 + 1
    return "10.{}.{}".format(n3, n2)


def calc_vpn_ip(idx, num):
    n2 = int((idx - 1) / 254) + 1
    n1 = (idx - 1) % 254 + 1
    return "172.{}.{}.{}".format(num, n2, n1)

_next_idx_sql_old = '''
SELECT  idx + 1
FROM    omixtory_{tab} mo
WHERE   NOT EXISTS
        (
        SELECT  NULL
        FROM    omixtory_{tab} mi 
        WHERE   mi.idx = mo.idx + 1
        )
ORDER BY
        idx
LIMIT 1
'''
