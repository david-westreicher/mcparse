{
    int i=1;
    int a=1;
    int b=1;
    int c=1;
    int d=1;
    if(1){
        b = 1;
        c = 1;
        d = 1;
    }else{
        a = 1;
        d = 1;
        if(1){
            d = 1;
        }else{
            c = 1;
        }
        b = 1;
    }
    int y = a + b;
    int z = c + d;
    i = i + 1;
}
