
float pi_odd(float i, float num_its) {
	if(i >= num_its) return 0.0;
	return (-4.0 /  (1.0 + (i*2.0))) + pi_even(i+1.0, num_its);
}
float pi_even(float i, float num_its) {
	if(i >= num_its) return 0.0;
	return (4.0 /  (1.0 + (i*2.0))) + pi_odd(i+1.0, num_its);
}

float pi(float num_its) {
	return pi_even(0.0, num_its);
}

void main() {	
	start_measurement();
	float res = pi(2000.0);
	end_measurement();
	print_float(res);
}
