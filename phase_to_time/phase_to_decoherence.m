% https://abracon.com/phase-noise-and-jitter-calculator# (series=ASA out=CMOS fc=12 VDD=1.8)
fc=12e6;  N=1000;
fF=  [10  100  1000  1e4  1e5  1e6  1e7  2E7];
SdBc=[-71 -102 -134 -150 -159 -161 -161 -162];
% dBc/Hz to dBrad^2/Hz
SdBrad=SdBc+3;
Srad=10.^(SdBrad/10);
% phase noise Sphi to fractional frequency spectral density Sy
Sy=Srad.*(fF.^2)/(fc^2);
SydB=10*log10(Sy);
% Sy interpolation: linear fit in the log-log scale (polynomial law)
Syint=[];
fFint=[];
for k=1:length(SdBc)-1
   Syint=[Syint SydB(k)+(SydB(k+1)-SydB(k))/(log10(fF(k+1))-log10(fF(k)))*(linspace(log10(fF(k)),log10(fF(k+1)),N)-log10(fF(k)))];
   fFint=[fFint 10.^(linspace(log10(fF(k)),log10(fF(k+1)),N))];
end
subplot(311);semilogx(fF,SdBc,'x-');xlabel('freq. offset (Hz)');ylabel('Sphi (dBc/Hz)')
subplot(312);semilogx(fFint,Syint+3,'.');hold on;semilogx(fF,SydB,'rx-');xlabel('freq. offset (Hz)');ylabel('Sy (dB/Hz)')
% back to linear domain for integration: Sy to AVAR and MVAR
Syint=10.^(Syint/10);
N=3
taurange=logspace(log10(N*0.45/fF(end)),log10(0.45/fF(1)/N),1024);
% the 0.45 comes from the AVAR and MVAR spectral response |H(f.\tau)|^2 maximum power, see
% https://rubiola.org/pdf-lectures/Scientific%20Instruments%20L06-10,%20Oscillators.pdf slide 3
%   "Two Sample (Allan-like) variances" chart
m=1;
for tau=taurange
   avar(m)=2*sum(Syint(1:end-1).*(fFint(2:end)-fFint(1:end-1)).*sin(pi*tau*fFint(1:end-1)).^4./(pi*tau*fFint(1:end-1)).^2);
   mvar(m)=2*sum(Syint(1:end-1).*(fFint(2:end)-fFint(1:end-1)).*sin(pi*tau*fFint(1:end-1)).^6./(pi*tau*fFint(1:end-1)).^4);
   cohT(m)=sum(Syint(1:end-1).*(fFint(2:end)-fFint(1:end-1)).*sin(pi*tau*fFint(1:end-1)).^2./(pi*tau*fFint(1:end-1)).^2);
   m=m+1;
end
subplot(313)
loglog(taurange,sqrt(avar),'.');xlabel('tau (s)');ylabel('ADEV (no unit)');
hold on
loglog(taurange,sqrt(mvar),'.');xlabel('tau (s)');ylabel('ADEV (no unit)');grid on;axis tight
k=find(taurange<=4E-6);a=polyfit(log(taurange(k)),log(sqrt(mvar(k))),1)  % -1.5 => ^2=-3 white PM: h2.f^2 -> 0.038*h2/tau^3
hold on
h2=exp(a(2))
k=find((taurange>4E-6) & (taurange<=4E-5));a=polyfit(log(taurange(k)),log(sqrt(mvar(k))),1) % -1   => ^2=-2: h1.f -> 0.0855*h1/tau^2
k=find((taurange>4E-5) & (taurange<=3E-4));a=polyfit(log(taurange(k)),log(sqrt(mvar(k))),1) % -0.5 => ^2=-1: h0   -> h0/3/tau
k=find(taurange>3E-4);a=polyfit(log(taurange(k)),log(sqrt(mvar(k))),1)                      % 0    => h-1/f       -> 0.75*h-1
loglog(taurange(k),sqrt(mvar(k)),'g.')
% https://rubiola.org/pdf-static/Enrico%27s-chart-EFTS.pdf

% Sy to coherence time C(T)
% <C^2(T)>=2/T\int (1-tau/T)exp[-(2*pi*nu0*tau)^2\int Sy(f).HI(f).df].dtau
figure
Trange=taurange;  

% problem of numerical integration boundaries: avoid impact of samples missing outside measurement range
k=find(Trange<1/fF(1)/50);Trange=Trange(k);
k=find(Trange>1/fF(end)*50);Trange=Trange(k);

for nu0=[490E6 490E7 490E8 100e9 190e9]
  clear C
  m=1;
  for T=Trange
    k=find(taurange<=T);
    if (k(end)==length(taurange)) k=k(1:end-1);end
    C(m)=2/T*sum((1-taurange(k)/T).*exp(-2*(pi*nu0*taurange(k)).^2.*cohT(k)).*(taurange(k+1)-taurange(k)));
    m=m+1;
  end
  semilogx(Trange,1-sqrt(C))
  hold on
end
xlabel('tau');ylabel('1-sqrt<C^2(T)>')
legend('490 MHz','4900 MHz','49000 MHz','100000 MHz','190000 MHz','location','north')
ylim([-0.05 1.05])
