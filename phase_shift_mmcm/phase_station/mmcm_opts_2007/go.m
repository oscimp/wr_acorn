close all
clear all
  
dirlist=dir('*tim');
leg=[];
for dirnum=1:length(dirlist)
  filename=dirlist(dirnum).name
  [freq,Sphi]=read_tim(filename);
  subplot(511)
  semilogx(freq,Sphi+3);hold on
%  leg=[leg, """", strrep(strrep(filename,'_',' '),'.tim',''),""","];
end
eval(["legend(",leg(1:end-1),");"]);
xlabel('frequency offset (Hz)')
ylabel('Sphi (dBrad^2/Hz)')
grid on
