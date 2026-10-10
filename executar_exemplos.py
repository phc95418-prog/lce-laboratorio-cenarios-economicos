"""Exemplos do Modulo 01, correspondentes a arquitetura LCE v1.1."""

from modelo_mercado import simular_mercado, parametros_por_elasticidades


def mostrar_tabela(titulo, cenarios):
    print("\n" + titulo)
    print("-" * 77)
    print(f"{'Cenario':<23} {'Q sem imp.':>10} {'Q com imp.':>11} "
          f"{'Arrec.':>10} {'Peso morto':>12}")
    for nome, parametros in cenarios:
        r = simular_mercado(**parametros)
        print(f"{nome:<23} {r['q0']:>10.1f} {r['qt']:>11.1f} "
              f"{r['arrecadacao']:>10.1f} {r['peso_morto']:>12.1f}")


def principal():
    base = simular_mercado(a=100, b=1, c=20, d=1, t=20)
    print("LCE - Modulo 01 | Primeira execucao")
    print("=" * 77)
    print("Exemplo de referencia (valores hipoteticos):")
    print(f"Equilibrio inicial: Q0={base['q0']:.0f}; P0={base['p0']:.0f}")
    print(f"Apos imposto: Qt={base['qt']:.0f}; Pc={base['pc']:.0f}; "
          f"Pp={base['pp']:.0f}")
    print(f"Reparticao do imposto: consumidor="
          f"{100*base['fracao_consumidor_efetiva']:.0f}%; produtor="
          f"{100*base['fracao_produtor_efetiva']:.0f}%")
    print(f"EC0={base['ec0']:.0f}; EP0={base['ep0']:.0f}; ET0={base['et0']:.0f}")
    print(f"EC={base['ec']:.0f}; EP={base['ep']:.0f}; "
          f"Arrecadacao={base['arrecadacao']:.0f}; "
          f"ET={base['et']:.0f}; Peso morto={base['peso_morto']:.0f}")

    experimento_a = [
        ("A - Simetrico", dict(a=100, b=1, c=20, d=1, t=20)),
        ("B - Demanda menos elast.", dict(a=120, b=1.5, c=40, d=0.5, t=20)),
        ("C - Oferta menos elast.", dict(a=80, b=0.5, c=0, d=1.5, t=20)),
    ]
    mostrar_tabela("Experimento A: quem suporta o imposto?", experimento_a)
    print("Parcelas suportadas pelo consumidor:")
    for nome, parametros in experimento_a:
        r = simular_mercado(**parametros)
        print(f"  {nome}: {100*r['fracao_consumidor_efetiva']:.0f}%")

    experimento_b = [
        ("B1 - Elasticidades 3.0", parametros_por_elasticidades(60, 40, 3, 3, 20)),
        ("B2 - Elasticidades 1.5", parametros_por_elasticidades(60, 40, 1.5, 1.5, 20)),
        ("B3 - Elasticidades 1.2", parametros_por_elasticidades(60, 40, 1.2, 1.2, 20)),
    ]
    mostrar_tabela("Experimento B: quanto o imposto distorce o mercado?", experimento_b)

    proibitivo = simular_mercado(a=100, b=1, c=20, d=1, t=90)
    print("\nImposto proibitivo (t=90):")
    print(f"Qt={proibitivo['qt']:.0f}; Pc={proibitivo['pc']}; "
          f"Pp={proibitivo['pp']}; Peso morto={proibitivo['peso_morto']:.0f}")


if __name__ == "__main__":
    principal()
