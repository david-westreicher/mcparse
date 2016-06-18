
float pi(float num_its) {
	float res = 0.0;
	for(float i = 0.0; i < num_its; i=i+2.0) {
		res = res + (4.0 /  (1.0 + (i*2.0)));
		res = res - (4.0 /  (1.0 + ((i+1.0)*2.0)));
	}
	return res;
}

void main() {	
	start_measurement();
	float res = pi(2000.0);
	end_measurement();
	print_float(res);
}
