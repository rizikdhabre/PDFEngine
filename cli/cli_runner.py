import argparse
import fitz
from core.signature_logic import choose_best_plan
from core.imposition import impose_A5_booklet, impose_A6_nup, impose_A7_nup

def run_cli():
    p = argparse.ArgumentParser(description='PDF imposition CLI')
    p.add_argument('src', help='Source PDF path')
    p.add_argument('--target', choices=['a5','a6','a7'], default='a5')
    args = p.parse_args()

    src = fitz.open(args.src)
    best, _ = choose_best_plan(len(src))
    if args.target == 'a5':
        out = impose_A5_booklet(src, best, None)
        suffix = '_A5_booklet_spreads.pdf'
    elif args.target == 'a6':
        out = impose_A6_nup(src, best, None)
        suffix = '_A6_4up.pdf'
    else:
        out = impose_A7_nup(src, best, None)
        suffix = '_A7_8up.pdf'

    out_path = args.src.rsplit('.',1)[0] + suffix
    out.save(out_path)
    out.close()
    print('Saved:', out_path)

if __name__ == '__main__':
    run_cli()
