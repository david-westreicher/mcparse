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
        int ten_even = is_even(10);
        int ten_odd = is_odd(10);
    }
}
