for f in bench/*.c
do
    filename=$(basename "$f")
    echo "util/build.py $f --lvn"
    util/build.py $f --lvn
done

for f in origbench/*.c
do
    filename=$(basename "$f")
    echo "gcc -o origbench/${filename%.c} $f assembler/lib.c -m32"
    gcc -o origbench/${filename%.c} $f assembler/lib.c -m32
done
