import os
from utils.sanitizacao import sanitizar_nome_arquivo

def exportar_csv(df,pasta,gid,nome_aba):
    
    os.makedirs(pasta,exist_ok=True)
    fNome  =  (
            f"{sanitizar_nome_arquivo(gid)}"
            f"_{sanitizar_nome_arquivo(nome_aba)}")
    arquivo = os.path.join(pasta,f"{fNome}.csv"    )
    df.to_csv(arquivo,sep=";",encoding="utf-8-sig",index=False)
    return arquivo