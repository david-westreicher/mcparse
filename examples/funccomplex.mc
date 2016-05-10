{
    int plus(int x, int y){
        int sum = 0;
        for(int i=0;i<x+y;i=i+1){
            sum = sum+x+y;
        }
        return sum;
    }
    int times(int x, int y){
        int product = 1;
        for(int i=0;i<x+y;i=i+1){
            product = product*(x+y);
        }
        return product;
    }

    int two_plus_three = plus(2,3);
    int two_times_three= times(2,3);
}
