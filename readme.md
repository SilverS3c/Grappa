## Set up test/demo environment

0. Install terraform, kubectl, helm
1. Clone Grappa repository
2. cd Grappa/infra/Digitalocecan/Terraform
3. Write DigitalOcean Token to "terraform.tfvars" (key: do_token); example: echo 'do_token = "dop_v1_[REDACTED]"' > terraform.tfvars
4. terraform init
5. terraform apply -var "kubeconfig_filename=~/kubeconfig" -auto-approve	(This is going to take a while (~5m))
6. helm --kubeconfig=~/kubeconfig install grappa-infra ../Helm
7. Find LoadBalancer's ip from DigitalOcean
8. Copy IP to a browser's address bar
9. Log in with username: admin and password: MIKPassword111
10. Home -> Connections -> Data Sources -> Add Data Source
11. Select JSON
12. Add details: 
	Name: Influx
	URL: http://grappa:5000
	Turn on "Basic Auth" and "With Credentials"
	username: test, password: asd
13. Save and test
14. Repeat the steps with the following details:
	name: Mysql
	URL: http://grappa-mysql:5001
	Rest are the same
15. Save and test
16. Add new Data Source -> Prometheus, url: http://prometheus:9090
17. Save and test
18. Home -> Explore
19. We can run queries on the InfluxDB, MySQL and Prometheus server
