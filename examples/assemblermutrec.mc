{
    int is_even(int n){
        if (n!=0)
            return is_odd(n-1);
        return 1;
    }
    int is_odd(int n){
        if (n!=0)
            return is_even(n-1);
        return 0;
    }
    void main(){
        int x = read_int();
        print_int(is_even(x));
        print_int(is_odd(x));
    }
}
