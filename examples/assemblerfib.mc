{
    int nthfib(int n){
        int f1 = 0;
        int f2 = 1;
        for(int i=0;i<n;i=i+1){
            int nextfib = f1+f2;
            f1 = f2;
            f2 = nextfib;
        }
        return f1;
    }
    void main(){
        int fib = nthfib(read_int());
        print_int(fib);
    }
}
