{
    int nthfib = 10;
    int f1 = 0;
    int f2 = 1;
    int i;
    for(i=0;i<nthfib;i=i+1){
        int nextfib = f1+f2;
        f1 = f2;
        f2 = nextfib;
    }
    int fib = f1;
}
