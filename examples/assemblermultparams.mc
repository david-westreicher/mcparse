{
    int first(int x, int y, int z, int a, int b){
        return x;
    }
    int second(int x, int y, int z, int a, int b){
        return y;
    }
    int third(int x, int y, int z, int a, int b){
        return z;
    }
    int fourth(int x, int y, int z, int a, int b){
        return a;
    }
    int fifth(int x, int y, int z, int a, int b){
        return b;
    }
    int main(){
        print_int(first(1,2,3,4,5));
        print_int(second(1,2,3,4,5));
        print_int(third(1,2,3,4,5));
        print_int(fourth(1,2,3,4,5));
        print_int(fifth(1,2,3,4,5));
        return 0;
    }
}
