close all
clear all

fc=1e7; % carrier frequency
N=100;  % interpolation factor
% phase noise spectral SdBc @ fF
fF=  [1    10  100 1000 10000 1e5 1e6 1e7] % extend 100 kHz measurement floor to 10 MHz

% sanity check: 1/f, constant and f
SdBc(:,1)=[-70  -90  -90  -100 -110 -120 -130 -140]; % Sphi=1/f   => Sy~f   => AVAR~1/tau^2 MVAR~1/tau^2
SdBc(:,2)=[-100 -100 -100 -100 -100 -100 -100 -100]; % Sphi=cst   => Sy~f^2 => AVAR~1/tau^2 MVAR~1/tau^3
SdBc(:,3)=[-90  -110  -130 -150 -170 -190 -210 -230] % Sphi~1/f^2 => Sy~cst => AVAR~1/tau   MVAR~1/tau

%if (1==0)  % uncomment for sanity check
% WR specifications
SdBc(:,1)=[-70  -70  -95  -120 -130 -130 -130 -130]; % BC/GM class I
SdBc(:,2)=[-100 -100 -115 -130 -140 -140 -140 -140]; % GM class II (LJ)
SdBc(:,3)=[-90  -90  -107 -125 -135 -135 -135 -135]  % BC class II
%end

SdBrad=SdBc+3;      % dBc/Hz -> dBrad^2/Hz
%%%%%%%% interpolate, convert SdBc to SdBrad to Sy (linear) & integrate to AVAR
for count=1:3
  Sy=(10.^(SdBrad(:,count)/10))'.*(fF.^2)/(fc^2);
  Syint=[];
  fFint=[];
  for k=1:length(SdBc(:,count))-1
     Syint=[Syint Sy(k)+(Sy(k+1)-Sy(k))/(fF(k+1)-fF(k))*(linspace((fF(k)),(fF(k+1)),N)-fF(k))];
     % fFint=[fFint logspace(log10(fF(k)),log10(fF(k+1)),N)];
     fFint=[fFint linspace((fF(k)),(fF(k+1)),N)];
  end

  if (count==1)
    figure(1)
    subplot(211)
    semilogx(fF,(SdBrad(:,count)))
    hold on
    semilogx(fF,10*log10(Sy))
    xlabel('Fourier frequency (Hz)')
    ylabel('phase noise (dBc/Hz)');legend('Sphi','Sy=Sphixf^2','location','southwest')
    grid on
    title('Class I')
  end
  m=1;
  taurange=logspace(log10(1/fF(end)),log10(1/fF(1)),1024);
  for tau=taurange
% see https://rubiola.org/pdf-lectures/Scientific%20Instruments%20L06-10,%20Oscillators.pdf
% slide 49
    avar(m)=2*sum(Syint(1:end-1).*(fFint(2:end)-fFint(1:end-1)).*sin(pi*tau*fFint(1:end-1)).^4./(pi*tau*fFint(1:end-1)).^2);
% slide 51
    mvar(m)=2*sum(Syint(1:end-1).*(fFint(2:end)-fFint(1:end-1)).*sin(pi*tau*fFint(1:end-1)).^6./(pi*tau*fFint(1:end-1)).^4);
    m=m+1;
  end
  figure(99)
  subplot(211)
  % plot resulting adev=sqrt(avar)
  adev=sqrt(avar);
  loglog(taurange,adev)
  polyfit(log(taurange),log(adev),1)(1)
  xlabel('tau (s)');ylabel('ADEV (no unit)')
  grid on
  hold on
  
  figure(98)
  subplot(211)
  % plot resulting mdev=sqrt(mvar)
  mdev=sqrt(mvar);
  loglog(taurange,mdev)
  polyfit(log(taurange),log(mdev),1)(1)
  xlabel('tau (s)');ylabel('MDEV (no unit)')
  grid on
  hold on
end
legend('Class I','GM class II','BC class II')
figure(99)
legend('Class I','GM class II','BC class II')

% ADEV(1/f) = -0.9433
% MDEV(1/f) = -1.0258
% ADEV(cst) = -1.0006
% MDEV(cst) = -1.5117
% ADEV(f) = -0.5148
% MDEV(f) = -0.5383

