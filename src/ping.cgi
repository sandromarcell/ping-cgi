#!/bin/bash --norc
#
# Copyright 2017 Sandro Marcell <smarcell@mail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.
#
PATH='/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin'
RANDOM=$$

# Bloco(s) de rede(s) que sera(o) verificado(s)
# Obs.: Caso haja mais de uma, separe-as por espacos
REDES='192.168.1.0/24'

# Verifica se todos os comandos necessarios para o funcionamento do script
# estao instalados.
function verificarDependencias {
	local cmd
	for cmd in $@; do
		command -v $cmd > /dev/null 2>&1 || {
			echo '<p><strong>HTTP/1.1 500 Internal Server Error</strong></p>'
			echo "<p><small>${cmd}: command not found</small></p>"
			exit 1
		}
	done
}

# Funcao que faz o trabalho pesado... Rsrsrs verificando o bloco (ou blocos) de 
# rede, testando que esta on ou offline
# IMPORTANTE: Certifique-se que a(s) rede(s) tenha(m) permissao para responder
# a requisicoes do tipo ICMP!
function listarIPs {
	local arq_tmp ativos inativos contador status netbios classe 
	local -a ip

	arq_tmp="/tmp/$RANDOM"

	# Invalida qualquer dado enviado via POST que nao esteja no formato
	# CIDR (xxx.xxx.xxx.xxx/yy)
	echo "$1" | grep -Eoq '^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/([0-9]|[1-2][0-9]|3[0-2]))$' || {
		echo '<p><strong>HTTP/1.1 403 Forbidden</strong></p>'
		exit 1
	}

	# Listagem dos estados dos hosts na(s) rede(s)
	nmap -v -sn -oG - "$1" | stdbuf -o0 awk 'NR > 3 && NR <= 257 {print $2,$5}' > $arq_tmp	 
	ativos=$(grep -Fc 'Up' $arq_tmp)
	inativos=$(grep -Fc -v 'Up' $arq_tmp)

	echo "<tr><td>$rede</td><td>Ativa</td><td>$ativos</td><td>$inativos</td></tr></table><br />"
	echo '<span class="info">** Podem ocorrer "falsos dispon&iacute;veis" devido a poss&iacute;veis bloqueios do protocolo ICMP **</span>'

	cat <<-EoL
	<table class="bordered">
		<thead>
			<tr>
				<th>#</th>
				<th>IP</th>
				<th>Status</th>
				<th>Host</th>
			</tr>
		</thead>
	EoL
	
	# Verifica quais hosts estao on/off
	while IFS= read -r i; do
		((++contador))
		ip=($i)
		if [ ${ip[1]} = 'Up' ]; then
			status='Em uso'
			# Retorna o "NetBios Name" dos hosts online
			netbios=$(nbtscan -n -T 0.5 ${ip[0]} | stdbuf -o0 grep -Eo '\s(.+)?\\.+\s')
			[ -z "$netbios" ] && netbios='?'
			classe='used'
		else
			status='Dispon&iacute;vel'
			netbios=''
			classe='unused'
		fi
		echo "<tr><td>$contador</td><td>${ip[0]}</td><td><span class="\"$classe\"">$status</span></td><td>${netbios// }</td></tr>"
	done < $arq_tmp

	rm -f $arq_tmp

	return 0
}

# Retornando os resultados para o browser
echo -e "Content-type: text/html\n\n"
verificarDependencias 'grep' 'nmap' 'stdbuf' 'awk' 'cat' 'nbtscan'
cat <<-FIM
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
	<title>${0##*/}</title>
	<meta http-equiv="content-type" content="text/html;charset=utf-8" />
	<meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1" />
	<meta name="author" content="Sandro Marcell" />
	<meta name="generator" content="Geany 1.24.1" />
	<script type="text/javascript">
		function submeterFormulario() {
			document.getElementById("load").innerHTML = "<br /><span class='blink'><b>Gerando lista...</b></span>";
			document.forms[0].submit();
		}
	</script>
	<style type="text/css">
		body {
			width: 600px;
			margin: 40px auto;
			font-family: 'trebuchet MS', 'Lucida sans', Arial;
			font-size: 14px;
			color: #444;
		}

		table {
			*border-collapse: collapse; /* IE7 and lower */
			border-spacing: 0;
			width: 100%;    
		}

		span.info {
			color: #008000;
			margin: auto;
			display: table;
			font-size: 12px;
		}

		span.used { color: #ff0000; }
		span.unused { color: #008000; }
		
		span.blink {
			animation: blinking 1s linear infinite;
		}

		#load { text-align: center; }

		@keyframes blinking {
			50% { opacity: 0; }
		}

		.bordered {
			border: solid #ccc 1px;
			-moz-border-radius: 6px;
			-webkit-border-radius: 6px;
			border-radius: 6px;
			-webkit-box-shadow: 0 1px 1px #ccc; 
			-moz-box-shadow: 0 1px 1px #ccc; 
			box-shadow: 0 1px 1px #ccc;         
		}

		.bordered tr:hover {
			background: #fbf8e9;
			-o-transition: all 0.1s ease-in-out;
			-webkit-transition: all 0.1s ease-in-out;
			-moz-transition: all 0.1s ease-in-out;
			-ms-transition: all 0.1s ease-in-out;
			transition: all 0.1s ease-in-out;     
		}

		.bordered td, .bordered th {
			border-left: 1px solid #ccc;
			border-top: 1px solid #ccc;
			padding: 10px;
			text-align: center;    
		}

		.bordered th {
			background-color: #dce9f9;
			background-image: -webkit-gradient(linear, left top, left bottom, from(#ebf3fc), to(#dce9f9));
			background-image: -webkit-linear-gradient(top, #ebf3fc, #dce9f9);
			background-image: -moz-linear-gradient(top, #ebf3fc, #dce9f9);
			background-image: -ms-linear-gradient(top, #ebf3fc, #dce9f9);
			background-image: -o-linear-gradient(top, #ebf3fc, #dce9f9);
			background-image: linear-gradient(top, #ebf3fc, #dce9f9);
			-webkit-box-shadow: 0 1px 0 rgba(255,255,255,.8) inset; 
			-moz-box-shadow:0 1px 0 rgba(255,255,255,.8) inset;  
			box-shadow: 0 1px 0 rgba(255,255,255,.8) inset;        
			border-top: none;
			text-shadow: 0 1px 0 rgba(255,255,255,.5); 
		}

		.bordered td:first-child, .bordered th:first-child {
			border-left: none;
		}

		.bordered th:first-child {
			-moz-border-radius: 6px 0 0 0;
			-webkit-border-radius: 6px 0 0 0;
			border-radius: 6px 0 0 0;
		}

		.bordered th:last-child {
			-moz-border-radius: 0 6px 0 0;
			-webkit-border-radius: 0 6px 0 0;
			border-radius: 0 6px 0 0;
		}

		.bordered th:only-child{
			-moz-border-radius: 6px 6px 0 0;
			-webkit-border-radius: 6px 6px 0 0;
			border-radius: 6px 6px 0 0;
		}

		.bordered tr:last-child td:first-child {
			-moz-border-radius: 0 0 0 6px;
			-webkit-border-radius: 0 0 0 6px;
			border-radius: 0 0 0 6px;
		}

		.bordered tr:last-child td:last-child {
			-moz-border-radius: 0 0 6px 0;
			-webkit-border-radius: 0 0 6px 0;
			border-radius: 0 0 6px 0;
		}
	</style>
</head>
<body>
	<form action="" method="POST">
		<span><strong>Gerar lista de IP's:</strong></span>
		<select name="rede" onchange="submeterFormulario()">
			<option value="" selected="selected">Selecionar rede</option>
			$(for i in $REDES; do
				echo "<option value="\"$i\"">$i</option>"
			done)
		</select>
	</form>
	<div id="load"></div>
	<br />
	<table class="bordered">
			<thead>
				<tr>
					<th>Rede</th>
					<th>Status</th>
					<th>Em uso</th>
					<th>Dispon&iacute;veis</th>
				</tr>
			</thead>
			$(if [ "$REQUEST_METHOD" = 'POST' -a "$CONTENT_LENGTH" -gt 0 ]; then
				read -n $CONTENT_LENGTH POST <&0
				rede=$(echo $POST | stdbuf -o0 sed -e 's/\(.*=\)\(.*\)/\2/' -e 's/%2F/\//')
				listarIPs $rede
			fi)
	</table>
</body>
</html>
FIM

exit 0
