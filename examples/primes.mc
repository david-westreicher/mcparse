{
    int num = 50000;
    int prime;
    if(num<=1){
        prime = 1;
    }else{
        int i;
        int j;
        for(i=0;i<(num+1);i=i+1){
            int isprime = 1;
            for(j=2;j<i;j=j+1){
                if((i%j)==0){
                    isprime = 0;
                }
            }
            if(isprime){
                prime = i;
            }
        }
    }
}
