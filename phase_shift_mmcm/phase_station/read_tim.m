function [allfreq,allSphi,allSphifloor]=read_tim(filename)
  fid = fopen(filename, 'r');
  if fid == -1
    error('Cannot open file');
  end
  
  allfreq=[];
  allSphi=[];
  allSphifloor=[];
  do
    while true
      line = fgetl(fid);
      if ~isempty(strfind(line, 'FPN'))
        if isempty(strfind(line, ';'))
          break;
        end
      end
      if feof(fid)
        break
      end
    end
    if (~feof(fid))
      clear freq Sphi Sphifloor
      arg=strsplit(line," "); % ;FPN <Total bins for stage 0> <First visible bin> <Last visible bin> <# averages>
      % arg                   % display line with arguments
      N=str2num(arg{2});
      Nstart=str2num(arg{3});
      Nstop=str2num(arg{4});
      Navg=str2num(arg{5});
      for n=1:N
        line = fgetl(fid);    % <Offset> <PN> <PN floor> <AM> <AM floor>
        arg=strsplit(line," ");
        freq(n)=str2num(arg{2});
        Sphi(n)=str2num(arg{3});
        Sphifloor(n)=str2num(arg{4});
        line = fgetl(fid);    % <PN> for raw channel 0
        line = fgetl(fid);    % <PN> for raw channel 1
      end
      allfreq=[allfreq freq(Nstart:Nstop)];
      allSphi=[allSphi Sphi(Nstart:Nstop)];
      allSphifloor=[allSphifloor Sphifloor(Nstart:Nstop)];
    %  semilogx(freq(Nstart:Nstop),Sphi(Nstart:Nstop));hold on
    end
  until (feof(fid));
  [allfreq,ind]=sort(allfreq);
  allSphi=allSphi(ind);
  allSphifloor=allSphifloor(ind);
end
