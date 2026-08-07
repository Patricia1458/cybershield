import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Profile
from training.models import TrainingModule, QuizQuestion
from phishing.models import EmailTemplate, PhishingCampaign, PhishingResult

MODULES = [
    {
        'title': 'Recognizing Email Phishing Attempts',
        'category': 'phishing',
        'description': 'Learn to spot the warning signs of a phishing email before you click.',
        'content': (
            "Phishing is a type of cyberattack where an attacker impersonates a trusted organization or "
            "person, usually through email, to trick you into revealing sensitive information, clicking a "
            "malicious link, or downloading malware.\n\n"
            "How it works: Attackers craft emails that look like they come from a legitimate source, such as "
            "your bank, employer, or a well-known company. These emails often create a sense of urgency or "
            "fear, pressuring you to act quickly without stopping to verify the request. The email typically "
            "contains a link to a fake website designed to steal your login credentials, or an attachment "
            "containing malware.\n\n"
            "Common examples include: fake 'account suspended' notices asking you to log in urgently, fake "
            "invoices or payment requests from a 'vendor,' emails claiming you've won a prize, and messages "
            "impersonating your company's IT department asking you to 'verify' your password."
        ),
        'scenario': (
            "It's Monday morning and you're catching up on your inbox after a busy weekend, working through "
            "a backlog of messages before your first meeting. Between routine internal updates and a few "
            "newsletters, one message stands out because of its urgent subject line.\n\n"
            "You receive an email that appears to be from 'IT Support' with the subject line 'Urgent: Your "
            "Account Will Be Suspended.' The email says your company email account has been flagged for "
            "unusual activity and asks you to click a link within 24 hours to verify your identity, or your "
            "account will be permanently locked. The sender's address is it-support@techstart-secure-verify.com "
            "— close enough to a real IT address that it's easy to miss at a glance.\n\n"
            "Attacks like this rely on employees scanning quickly rather than reading carefully, especially "
            "early in the day or when juggling multiple tasks. Attackers count on the combination of urgency "
            "and a familiar-sounding sender name to short-circuit the moment of doubt where someone would "
            "normally stop and verify."
        ),
        'questions': [
            {
                'question_text': 'What is the biggest red flag in this scenario?',
                'option_a': 'The email uses formal language',
                'option_b': "The sender's domain is not the real company domain",
                'option_c': 'The email has a subject line',
                'option_d': 'The email was sent during work hours',
                'correct_option': 'b',
            },
            {
                'question_text': 'What should you do if you receive an email like this?',
                'option_a': 'Click the link immediately to avoid losing access',
                'option_b': 'Reply to the email asking for more information',
                'option_c': 'Verify by contacting IT directly through a known, separate channel',
                'option_d': 'Forward it to a coworker to check first',
                'correct_option': 'c',
            },
            {
                'question_text': "Why do attackers use urgency ('within 24 hours') in phishing emails?",
                'option_a': 'To comply with email regulations',
                'option_b': 'To pressure you into acting before thinking carefully',
                'option_c': "It's a technical requirement of email servers",
                'option_d': 'It has no real purpose',
                'correct_option': 'b',
            },
            {
                'question_text': 'A legitimate IT department would typically:',
                'option_a': 'Ask you to confirm your password by email',
                'option_b': 'Never contact you about account issues',
                'option_c': 'Direct you to official, verified internal channels rather than urgent email links',
                'option_d': 'Threaten immediate account suspension by email',
                'correct_option': 'c',
            },
            {
                'question_text': 'What does a mismatched sender domain usually indicate?',
                'option_a': 'A spelling mistake by IT',
                'option_b': 'A likely phishing attempt using a lookalike domain',
                'option_c': 'A new official company domain',
                'option_d': 'Nothing significant',
                'correct_option': 'b',
            },
        ],
    },
    {
        'title': 'Spotting Smishing (SMS Phishing) Attacks',
        'category': 'smishing',
        'description': 'Text message scams are increasingly common — learn how to identify them.',
        'content': (
            "Smishing is phishing conducted via SMS text message instead of email. Because text messages feel "
            "more personal and immediate than email, people are often less cautious with them, which attackers "
            "exploit.\n\n"
            "How it works: Attackers send texts impersonating banks, delivery companies, payroll systems, or "
            "government agencies, usually containing a shortened or suspicious link and a false sense of "
            "urgency.\n\n"
            "Common examples: fake delivery notifications asking you to 'reschedule' via a link, fake bank "
            "fraud alerts asking you to 'verify' by clicking, and fake payroll messages about a 'failed direct "
            "deposit.'"
        ),
        'scenario': (
            "You're on your lunch break, scrolling through your phone between meetings, when a text message "
            "notification appears. Payday is coming up in a few days, so a message mentioning payroll "
            "immediately catches your attention.\n\n"
            "The text reads: 'TechStart Payroll: Your direct deposit failed. Update your banking details "
            "within 2 hours to avoid a delay in your paycheck: bit.ly/techstart-payroll-fix'. The message "
            "came from an unknown number, not a saved contact, and the shortened link doesn't show where it "
            "actually leads.\n\n"
            "Smishing messages like this are effective because text messages feel more personal and "
            "time-sensitive than email, and most people are used to tapping links on their phones without a "
            "second thought. The combination of a financial concern and a tight deadline is designed to make "
            "you act on your phone, away from the more cautious habits you might have at your work computer."
        ),
        'questions': [
            {
                'question_text': 'What makes this text message suspicious?',
                'option_a': 'It mentions payroll',
                'option_b': 'It uses a shortened, unfamiliar link and creates urgency',
                'option_c': 'It was sent in the morning',
                'option_d': "It's addressed to 'you'",
                'correct_option': 'b',
            },
            {
                'question_text': 'What is a shortened link commonly used for in smishing attacks?',
                'option_a': 'Making links load faster',
                'option_b': 'Hiding the real, potentially malicious destination of a link',
                'option_c': 'Reducing text message character limits only',
                'option_d': "Nothing suspicious, it's standard practice",
                'correct_option': 'b',
            },
            {
                'question_text': 'What should you do if you receive this message?',
                'option_a': "Click the link to check if it's real",
                'option_b': "Reply 'STOP' to unsubscribe",
                'option_c': 'Contact your actual payroll/HR department directly using known contact details',
                'option_d': 'Forward your bank details to confirm',
                'correct_option': 'c',
            },
            {
                'question_text': 'Why are smishing attacks often effective?',
                'option_a': 'People tend to trust text messages more and act on them quickly',
                'option_b': 'Phones cannot receive spam',
                'option_c': 'Text messages are always verified by carriers',
                'option_d': 'They are illegal so people trust them',
                'correct_option': 'a',
            },
            {
                'question_text': 'A legitimate company needing to update your banking details would typically:',
                'option_a': 'Text you a link with a countdown timer',
                'option_b': 'Direct you to log in through their official app or website directly',
                'option_c': 'Ask for your bank PIN over text',
                'option_d': 'Never need to update banking details',
                'correct_option': 'b',
            },
        ],
    },
    {
        'title': 'Defending Against Vishing (Voice Phishing) Calls',
        'category': 'vishing',
        'description': "Phone-based scams can be highly convincing — here's how to protect yourself.",
        'content': (
            "Vishing is phishing conducted over a phone call. Attackers rely on a confident, authoritative "
            "tone and manufactured urgency to pressure victims into revealing sensitive information "
            "verbally.\n\n"
            "How it works: Attackers may impersonate your bank's fraud department, a government agency, or "
            "internal IT/HR staff, often using caller ID spoofing. They typically ask for account numbers, "
            "PINs, one-time passcodes, or remote access to your computer.\n\n"
            "Common examples: fake bank fraud department calls, fake tech support calls claiming your computer "
            "is infected, and fake calls from 'HR' asking you to confirm your bank details for payroll."
        ),
        'scenario': (
            "Your phone rings while you're at your desk, and the caller ID shows a number that looks like it "
            "could be a legitimate customer service line. You answer, and the person on the other end "
            "introduces themselves as a representative from your bank's fraud prevention team.\n\n"
            "The caller states there has been suspicious activity on your account and asks you to confirm "
            "your full card number and PIN 'to verify your identity and stop the fraudulent transaction "
            "immediately.' Their tone is calm but insistent, and background call-center noise makes the call "
            "feel routine and legitimate.\n\n"
            "Vishing calls succeed because a live human voice applying gentle pressure is harder to dismiss "
            "than a suspicious email sitting in an inbox. Attackers often rely on the victim's instinct to be "
            "polite and cooperative on the phone, especially when the caller claims to be protecting them "
            "from a supposed ongoing fraud."
        ),
        'questions': [
            {
                'question_text': 'What is the major warning sign in this call?',
                'option_a': 'The caller mentioned fraud prevention',
                'option_b': 'A legitimate bank asking for your full PIN over the phone',
                'option_c': 'The call came during business hours',
                'option_d': 'The caller had a professional tone',
                'correct_option': 'b',
            },
            {
                'question_text': 'What should you do if you receive a call like this?',
                'option_a': 'Provide the information quickly to stop the fraud',
                'option_b': 'Hang up and call your bank directly using the number on your card',
                'option_c': 'Ask the caller to email you instead',
                'option_d': 'Give a partial PIN to test them',
                'correct_option': 'b',
            },
            {
                'question_text': "Why do vishing attackers create urgency about 'stopping fraud immediately'?",
                'option_a': 'Banks require immediate verbal confirmation',
                'option_b': 'To prevent you from pausing to verify their legitimacy',
                'option_c': 'It speeds up call center processing',
                'option_d': "It's a standard banking procedure",
                'correct_option': 'b',
            },
            {
                'question_text': 'Which information should you never share over an unsolicited call?',
                'option_a': 'Your name',
                'option_b': 'Your full PIN or card security code',
                'option_c': 'The city you live in',
                'option_d': 'Your job title',
                'correct_option': 'b',
            },
            {
                'question_text': 'A genuine bank fraud department would typically:',
                'option_a': "Ask for your full PIN to 'confirm' your identity",
                'option_b': 'Already have your account details and never need your PIN read aloud',
                'option_c': "Threaten to freeze your account immediately if you don't comply",
                'option_d': 'Call from a blocked or unknown number only',
                'correct_option': 'b',
            },
        ],
    },
    {
        'title': 'Understanding Social Engineering Tactics',
        'category': 'social_engineering',
        'description': 'Learn how attackers manipulate people, not just systems, to gain access.',
        'content': (
            "Social engineering is the psychological manipulation of people into performing actions or "
            "divulging confidential information, rather than breaking through technical security measures. "
            "Attackers exploit human tendencies like trust, fear, curiosity, and the desire to be helpful.\n\n"
            "Common techniques include: pretexting, baiting, tailgating, and impersonation.\n\n"
            "Common examples: someone calling and claiming to be 'from head office' needing an urgent password "
            "reset, a stranger asking an employee to hold the door to a secure area, and an unfamiliar USB "
            "drive left in the break room labeled 'Salaries 2024.'"
        ),
        'scenario': (
            "It's a busy afternoon in the office, and you're heading back from the break room when you "
            "notice someone in the lobby who doesn't look familiar. They're dressed professionally, carrying "
            "a clipboard, and appear to be waiting near the secure door.\n\n"
            "A person you don't recognize approaches you directly. They say they're from 'corporate IT "
            "audit' and need you to walk them through the server room, claiming your usual badge reader is "
            "being tested and isn't working today — so they're relying on an employee to grant access "
            "instead.\n\n"
            "This kind of approach works because most people don't want to seem unhelpful or suspicious of "
            "someone who appears confident and professionally dressed. Attackers who use pretexting like "
            "this are counting on politeness and a desire to avoid an awkward confrontation to override an "
            "employee's better judgment about verifying identity first."
        ),
        'questions': [
            {
                'question_text': 'What social engineering technique is being used here?',
                'option_a': 'Baiting',
                'option_b': 'Impersonation/pretexting',
                'option_c': 'Smishing',
                'option_d': 'Vishing',
                'correct_option': 'b',
            },
            {
                'question_text': 'What should you do in this situation?',
                'option_a': 'Let them in since they seem professional',
                'option_b': 'Verify their identity through official channels before granting any access',
                'option_c': 'Ask a coworker to escort them instead',
                'option_d': "Assume it's fine since they mentioned IT audit",
                'correct_option': 'b',
            },
            {
                'question_text': "Why is 'tailgating' into secure areas a security risk?",
                'option_a': 'It slows down foot traffic',
                'option_b': 'It allows unauthorized people to bypass physical access controls',
                'option_c': "It's only a minor inconvenience",
                'option_d': "It's not actually a security risk",
                'correct_option': 'b',
            },
            {
                'question_text': 'Finding an unlabeled USB drive in the office, you should:',
                'option_a': "Plug it in to see what's on it",
                'option_b': 'Give it to IT/security without plugging it in',
                'option_c': 'Take it home',
                'option_d': 'Ignore it completely',
                'correct_option': 'b',
            },
            {
                'question_text': 'Social engineering attacks primarily exploit:',
                'option_a': 'Software vulnerabilities',
                'option_b': 'Human psychology and trust',
                'option_c': 'Network hardware flaws',
                'option_d': 'Encryption weaknesses',
                'correct_option': 'b',
            },
        ],
    },
    {
        'title': 'Building Strong Password Habits',
        'category': 'password_security',
        'description': 'Simple habits that dramatically reduce your risk of account compromise.',
        'content': (
            "Weak or reused passwords are one of the most common causes of account compromise. A strong "
            "password is long (at least 12 characters), unique to each account, and not based on easily "
            "guessable personal information.\n\n"
            "Password managers allow you to use a different strong password for every account without needing "
            "to memorize them all. Multi-factor authentication (MFA) adds a second layer of protection.\n\n"
            "Common mistakes: reusing the same password across work and personal accounts, writing passwords "
            "on sticky notes, and sharing passwords over chat or email 'just this once.'"
        ),
        'scenario': (
            "It's the end of the month, and reports are due soon. You're focused on your own deadline when a "
            "Slack notification pops up from a colleague on another team — someone you recognize but don't "
            "work with closely.\n\n"
            "They explain that their account for the shared reporting tool is locked and they have a "
            "deadline in ten minutes. They ask if they can borrow your login 'just for five minutes' to pull "
            "the numbers they need, promising to log out right after and not change anything.\n\n"
            "Requests like this are common precisely because they come from someone familiar, framed as a "
            "small, time-limited favor rather than an obvious security violation. The pressure of a shared "
            "deadline and the desire to help a colleague can make it feel easier to just hand over a password "
            "than to explain why that's not something you can do — even when the request turns out to be "
            "completely genuine, the right response is still the same."
        ),
        'questions': [
            {
                'question_text': 'What should you do in this situation?',
                'option_a': "Share your password since it's urgent",
                'option_b': 'Decline and direct them to IT for an account reset instead',
                'option_c': 'Share it but change it right after',
                'option_d': 'Ask them to promise not to change anything',
                'correct_option': 'b',
            },
            {
                'question_text': 'Why is password reuse across accounts risky?',
                'option_a': 'It saves time',
                'option_b': 'If one account is breached, all accounts using that password become vulnerable',
                'option_c': 'It has no real risk',
                'option_d': 'It is required by most companies',
                'correct_option': 'b',
            },
            {
                'question_text': 'What makes multi-factor authentication (MFA) effective?',
                'option_a': 'It replaces the need for a password entirely',
                'option_b': 'It requires a second proof of identity even if the password is stolen',
                'option_c': 'It makes login slower for no benefit',
                'option_d': 'It is only useful for banking apps',
                'correct_option': 'b',
            },
            {
                'question_text': 'A strong password is best described as:',
                'option_a': 'Short and easy to remember',
                'option_b': 'Long, unique per account, and not based on personal info',
                'option_c': 'The same one used everywhere for consistency',
                'option_d': 'Based on your birthday for easy recall',
                'correct_option': 'b',
            },
            {
                'question_text': 'Writing your password on a sticky note on your monitor is:',
                'option_a': 'A good backup method',
                'option_b': 'A physical security risk since anyone nearby can see it',
                'option_c': "Fine as long as it's a strong password",
                'option_d': 'Recommended by most IT departments',
                'correct_option': 'b',
            },
        ],
    },
    {
        'title': 'Recognizing Pop-up Phishing',
        'category': 'popup_phishing',
        'description': 'Fake pop-up alerts trick users into calling scammers or downloading malware.',
        'content': (
            "Pop-up phishing uses fake browser or system pop-up windows to trick users into believing "
            "their device is infected or their account is compromised, pressuring them to call a fake "
            "support number, download 'security software' (actually malware), or enter credentials into a "
            "fake login box.\n\n"
            "How it works: These pop-ups often appear while browsing, sometimes triggered by a malicious ad "
            "or compromised website, and mimic the look of real antivirus alerts, browser warnings, or "
            "system messages. They frequently use urgent, alarming language and countdown timers to pressure "
            "quick action.\n\n"
            "Common examples: a pop-up claiming 'Your computer is infected with 5 viruses, call this number "
            "now,' a fake 'Your Windows license has expired' message, and fake browser update prompts that "
            "actually install malware."
        ),
        'scenario': (
            "You're researching a work resource online, switching between a few browser tabs, when your "
            "screen is suddenly taken over by a full-screen alert. The layout looks similar to a real system "
            "warning, complete with familiar-looking logos and alarming red text.\n\n"
            "The pop-up claims: 'WARNING: Your computer is infected with a virus. Call Microsoft Support "
            "immediately at the number below to prevent data loss.' A countdown timer ticks down in the "
            "corner, and clicking the usual close button doesn't seem to make the window go away.\n\n"
            "Pop-ups like this are built to mimic the visual style of legitimate security software "
            "convincingly enough that even careful users can be startled into acting quickly. The countdown "
            "timer and the claim of imminent data loss are deliberately designed to short-circuit calm "
            "decision-making, pushing you toward calling a number that connects straight to a scammer rather "
            "than any real support line."
        ),
        'questions': [
            {
                'question_text': 'What is the safest response to this pop-up?',
                'option_a': 'Call the number immediately',
                'option_b': "Close the browser/tab without calling or clicking anything, then run your organization's actual antivirus software separately",
                'option_c': "Enter your password to 'verify' as instructed",
                'option_d': "Download the suggested 'fix' tool",
                'correct_option': 'b',
            },
            {
                'question_text': 'Why do these pop-ups use countdown timers?',
                'option_a': "It's a technical browser requirement",
                'option_b': 'To create panic and pressure quick, unthinking action',
                'option_c': 'To show how fast your internet is',
                'option_d': 'They have no real purpose',
                'correct_option': 'b',
            },
            {
                'question_text': 'Real antivirus/security warnings from your actual IT department would typically:',
                'option_a': 'Appear as random browser pop-ups with phone numbers',
                'option_b': 'Come through official, verified company channels',
                'option_c': 'Ask you to call an unfamiliar number',
                'option_d': 'Demand immediate payment',
                'correct_option': 'b',
            },
            {
                'question_text': 'What should you do if closing the pop-up is difficult?',
                'option_a': 'Keep clicking until it works',
                'option_b': 'Force-close the browser entirely (e.g. via task manager) rather than interacting with the pop-up',
                'option_c': 'Call the number to ask them to stop it',
                'option_d': "Restart and hope it's gone",
                'correct_option': 'b',
            },
            {
                'question_text': 'Fake pop-up phishing often impersonates:',
                'option_a': 'Only government agencies',
                'option_b': 'Antivirus software, browsers, or operating system alerts',
                'option_c': 'Only banks',
                'option_d': 'Nothing specific',
                'correct_option': 'b',
            },
        ],
    },
    {
        'title': 'Understanding Evil Twin Phishing',
        'category': 'evil_twin_phishing',
        'description': 'Fake Wi-Fi networks that look legitimate can intercept your data.',
        'content': (
            "Evil twin phishing involves an attacker setting up a fake Wi-Fi access point with a name (SSID) "
            "designed to look identical or very similar to a legitimate, trusted network — such as a coffee "
            "shop's real Wi-Fi or your office guest network. When a victim connects to the fake network, the "
            "attacker can intercept traffic, capture login credentials, or redirect them to fake login "
            "pages.\n\n"
            "How it works: Attackers often set up the evil twin network in the same physical location as the "
            "real one, sometimes with a stronger signal, making it more likely to be auto-selected by devices "
            "with 'connect to known networks' enabled. Once connected, all unencrypted traffic can "
            "potentially be monitored.\n\n"
            "Common examples: a fake 'Free Airport WiFi' network at a terminal, a fake network named nearly "
            "identically to a real office's guest network (e.g. 'CompanyGuest' vs 'Company-Guest'), and fake "
            "captive portal login pages that harvest credentials."
        ),
        'scenario': (
            "You've stopped at a coffee shop near the office to get some work done before your next meeting. "
            "After ordering, you open your laptop and check the available Wi-Fi networks so you can reply to "
            "a few emails while you wait.\n\n"
            "You see two networks listed: 'CoffeeShop_Free' and 'CoffeeShop_FreeWiFi.' Neither requires a "
            "password, and there's nothing posted in the shop telling you which one is official. Wanting to "
            "check work email quickly before your meeting, you connect to one of them without asking staff "
            "which is correct.\n\n"
            "Evil twin networks are especially common in places like cafes and airports, where open, "
            "password-free Wi-Fi is already the norm and people don't think twice before connecting. Because "
            "the fake network can be set up by anyone nearby with basic equipment, the only real way to tell "
            "it apart from the legitimate one is to verify the exact name with staff or avoid sensitive tasks "
            "on any unverified public network altogether."
        ),
        'questions': [
            {
                'question_text': 'What is the safest approach in this situation?',
                'option_a': 'Connect to whichever network has a stronger signal',
                'option_b': "Ask staff directly which network name is the official one, or use your phone's mobile hotspot instead for anything work-related",
                'option_c': 'Connect to both to compare',
                'option_d': "Assume both are safe since they're in a coffee shop",
                'correct_option': 'b',
            },
            {
                'question_text': 'Why are evil twin networks dangerous?',
                'option_a': 'They use more battery',
                'option_b': 'They can allow an attacker to intercept your traffic and credentials',
                'option_c': "They're slower than real WiFi",
                'option_d': 'They have no real risk',
                'correct_option': 'b',
            },
            {
                'question_text': 'A sign a WiFi network might be an evil twin is:',
                'option_a': 'It requires a password',
                'option_b': 'A name nearly identical to a known legitimate network, with no password required',
                'option_c': "It's listed first in the WiFi menu",
                'option_d': 'It has full signal bars',
                'correct_option': 'b',
            },
            {
                'question_text': 'For sensitive work tasks on public WiFi, you should:',
                'option_a': 'Use any open network available',
                'option_b': 'Use a company VPN if available, or avoid sensitive tasks entirely on unverified public networks',
                'option_c': 'Turn off your firewall for better speed',
                'option_d': 'Share the network with coworkers',
                'correct_option': 'b',
            },
            {
                'question_text': 'Evil twin attacks primarily target:',
                'option_a': 'Physical office doors',
                'option_b': 'Wireless network connections',
                'option_c': 'Phone SIM cards',
                'option_d': 'Email servers only',
                'correct_option': 'b',
            },
        ],
    },
]

BEST_PRACTICES_TEXT = (
    "Best Practices for Preventing Phishing Attacks\n\n"
    "Pay Attention to the Language in Emails: Social engineering exploits human fallibility, especially "
    "when people feel rushed. Be alert to a fake order (impersonating a courier to steal login "
    "credentials), business email compromise (impersonating an executive to instruct urgent action), and "
    "fake invoices (requesting payment redirected to an attacker's account). If a message urges immediate "
    "action, slow down and verify its authenticity before acting.\n\n"
    "Ongoing Training: Awareness training should be continuous, not a one-time event, using engaging "
    "material like visual guides. Employees should have clear steps to follow when a message seems "
    "suspicious.\n\n"
    "Phishing Drills: Regular simulated phishing campaigns (like the ones on this platform) help ensure "
    "training is actually applied. Drills work best when framed positively — as a challenge to spot the "
    "fake, with constructive feedback and encouragement for anyone who doesn't spot it, rather than "
    "punishment. Aim for drills roughly monthly."
)

TEMPLATES = [
    {
        'name': 'Account Verification Alert',
        'subject_line': 'Urgent: Your Account Will Be Suspended',
        'sender_name': 'IT Support',
        'sender_email': 'it-support@techstart-secure-verify.com',
        'channel': 'email',
        'difficulty': 'easy',
        'body_content': (
            "Dear Employee,\n\nYour account requires immediate verification. Our security systems have "
            "detected unusual login activity, and your account will be disabled within 24 hours if you do "
            "not verify your identity.\n\nTo avoid disruption, please [LINK]verify your account here[/LINK] and "
            "enter your credentials immediately to keep your account active."
        ),
    },
    {
        'name': 'Payroll Update Notice',
        'subject_line': 'Direct Deposit Failed - Action Required',
        'sender_name': 'Payroll Team',
        'sender_email': 'payroll@techstart-sme.example',
        'channel': 'sms',
        'difficulty': 'easy',
        'body_content': (
            "TechStart Payroll: Your direct deposit failed to process. Update your banking details within "
            "2 hours to avoid a delay in your paycheck: [LINK]bit.ly/payroll-update-now[/LINK]"
        ),
    },
    {
        'name': 'IT Password Reset',
        'subject_line': 'Password Expiring Soon',
        'sender_name': 'IT Helpdesk',
        'sender_email': 'it-helpdesk@techstart-sme.example',
        'channel': 'voice',
        'difficulty': 'easy',
        'body_content': (
            "Hello, this is IT Support calling about your account. Your password will expire within 24 "
            "hours and you will lose access to company systems. Please call us back immediately at "
            "[LINK]1-800-555-0198[/LINK] and have your current password ready so we can verify your identity."
        ),
    },
    {
        'name': 'Vendor Invoice Notice',
        'subject_line': 'Invoice #48213 - Payment Due',
        'sender_name': 'Vendor Partner Solutions - Billing',
        'sender_email': 'billing@vendorpartrner.com',
        'channel': 'email',
        'difficulty': 'hard',
        'body_content': (
            "Hello,\n\nAttached is invoice #48213 for the consulting services completed last month, "
            "totaling $4,250.00. As per our agreement, payment terms are net 15 days from the invoice "
            "date.\n\nWe would appreciate remittance at your earliest convenience — you can review the "
            "invoice and submit payment through [LINK]our secure billing portal[/LINK]. If you have any "
            "questions regarding this invoice or need our updated banking details, please don't hesitate to "
            "reach out.\n\nBest regards,\nBilling Department\nVendor Partner Solutions"
        ),
    },
    {
        'name': 'Prize Notification',
        'subject_line': "CONGRATULATIONS! You've Won a $500 Gift Card!",
        'sender_name': 'Rewards Center',
        'sender_email': 'prizes@reward-claim-center.net',
        'channel': 'email',
        'difficulty': 'easy',
        'body_content': (
            "CONGRATULATIONS!!!\n\nYour email address has been randomly selected to receive a $500 gift "
            "card! This is a limited-time offer and you must claim your prize within 24 hours or it will be "
            "forfeited.\n\n[LINK]Claim your gift card now[/LINK] — you will just need to enter some "
            "basic information to verify your identity and select your preferred gift card.\n\nDon't miss "
            "out on this amazing opportunity!"
        ),
    },
    {
        'name': 'MFA Confirmation Text',
        'subject_line': 'Verification Code Confirmation',
        'sender_name': 'Security Alerts',
        'sender_email': 'alerts@techstart-security.example',
        'channel': 'sms',
        'difficulty': 'hard',
        'body_content': (
            "Hi, this is a quick security check — we noticed a login attempt on your account. To confirm "
            "it's really you, please [LINK]verify your recent sign-in[/LINK] or reply with the 6-digit code "
            "we just sent you. If you didn't request this, reply STOP."
        ),
    },
    {
        'name': 'Delivery Failure Notice',
        'subject_line': 'Package Delivery Failed',
        'sender_name': 'Package Delivery',
        'sender_email': 'noreply@fast-track-delivery.example',
        'channel': 'sms',
        'difficulty': 'easy',
        'body_content': (
            "Your package could not be delivered due to an incomplete address. Reschedule delivery within "
            "24 hrs or it will be returned to sender: [LINK]track-redelivery-now.info/pkg[/LINK]"
        ),
    },
    {
        'name': 'IT Maintenance Callback',
        'subject_line': 'Routine Maintenance Callback',
        'sender_name': 'IT Operations',
        'sender_email': 'it-ops@techstart-sme.example',
        'channel': 'voice',
        'difficulty': 'hard',
        'body_content': (
            "Hi, this is IT Operations. We're doing some routine maintenance on our systems tonight and "
            "wanted to confirm a few account details before we proceed, just to make sure nothing gets "
            "disrupted for your team. When you get a chance, give us a call back at [LINK]1-800-555-0173[/LINK] "
            "and reference your extension so we can match up the right account. No rush, just wanted to touch "
            "base before the maintenance window. Thanks."
        ),
    },
    {
        'name': 'Urgent Wire Transfer Request',
        'subject_line': 'Urgent Wire Transfer Required',
        'sender_name': 'Executive Office',
        'sender_email': 'exec-office@techstart-sme.example',
        'channel': 'voice',
        'difficulty': 'easy',
        'body_content': (
            "This is an urgent message from the executive office. We need you to process a wire transfer "
            "immediately for a confidential business deal that is closing today. This is extremely "
            "time-sensitive and must be handled before end of day. Please call back right away at "
            "[LINK]1-800-555-0184[/LINK], and do not discuss this with anyone else in the office. Time is "
            "critical."
        ),
    },
]

CAMPAIGNS = [
    {'name': 'Q1 Email Phishing Test', 'template_name': 'Account Verification Alert'},
    {'name': 'Smishing Awareness Drill', 'template_name': 'Payroll Update Notice'},
    {'name': 'Vishing Response Test', 'template_name': 'IT Password Reset'},
    {'name': 'Vendor Invoice Test (Hard)', 'template_name': 'Vendor Invoice Notice'},
    {'name': 'Prize Notification Drill', 'template_name': 'Prize Notification'},
    {'name': 'MFA Code Confirmation Test (Hard)', 'template_name': 'MFA Confirmation Text'},
    {'name': 'Package Delivery Drill', 'template_name': 'Delivery Failure Notice'},
    {'name': 'IT Maintenance Callback Test (Hard)', 'template_name': 'IT Maintenance Callback'},
    {'name': 'Executive Wire Transfer Drill', 'template_name': 'Urgent Wire Transfer Request'},
]


class Command(BaseCommand):
    help = 'Seeds 7 training modules with quizzes AND 3 phishing campaigns with varied employee results.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Part 1 — Training content'))
        modules_created, questions_created, practices_backfilled, scenarios_expanded = self._seed_modules()

        self.stdout.write(self.style.MIGRATE_HEADING('\nPart 2 — Phishing simulation data'))
        templates_created, templates_fixed = self._seed_templates()
        campaigns_created, campaigns_fixed, campaigns = self._seed_campaigns()
        results_created = self._seed_results(campaigns)
        demo_fixes = self._ensure_demoable_unactioned_result(campaigns)

        employees = list(
            Profile.objects.filter(role='employee').values_list('user__username', flat=True)
        )

        self.stdout.write(self.style.SUCCESS(
            "\n" + "=" * 60 +
            "\nSEED SUMMARY" +
            "\n" + "=" * 60 +
            f"\nTraining modules created: {modules_created}"
            f"\nQuiz questions created: {questions_created}"
            f"\nExisting modules backfilled with best_practices: {practices_backfilled}"
            f"\nExisting modules with scenario expanded: {scenarios_expanded}"
            f"\nEmail templates created: {templates_created}"
            f"\nExisting templates corrected: {templates_fixed}"
            f"\nPhishing campaigns created: {campaigns_created}"
            f"\nExisting campaigns reassigned to correct template: {campaigns_fixed}"
            f"\nPhishing results created: {results_created}"
            f"\nExisting results reset to 'unactioned' for demo purposes: {demo_fixes}"
            f"\n\nEmployee usernames ({len(employees)} total) — log in as any of these to demo:"
            f"\n  {', '.join(employees)}"
        ))

    # ---- Part 1: training modules ----

    def _seed_modules(self):
        modules_created = 0
        questions_created = 0
        practices_backfilled = 0
        scenarios_expanded = 0

        for spec in MODULES:
            existing = TrainingModule.objects.filter(title=spec['title']).first()
            if existing:
                self.stdout.write(f"  Skipping module (already exists): {spec['title']}")
                update_fields = []
                if not existing.best_practices:
                    existing.best_practices = BEST_PRACTICES_TEXT
                    update_fields.append('best_practices')
                    practices_backfilled += 1
                    self.stdout.write(f"    Backfilled best_practices for: {spec['title']}")
                if existing.scenario != spec['scenario']:
                    existing.scenario = spec['scenario']
                    update_fields.append('scenario')
                    scenarios_expanded += 1
                    self.stdout.write(f"    Expanded scenario for: {spec['title']}")
                if update_fields:
                    existing.save(update_fields=update_fields)
                continue

            module = TrainingModule.objects.create(
                title=spec['title'],
                category=spec['category'],
                description=spec['description'],
                content=spec['content'],
                scenario=spec['scenario'],
                best_practices=BEST_PRACTICES_TEXT,
            )
            modules_created += 1
            self.stdout.write(f"  Created module: {module.title}")

            for q in spec['questions']:
                QuizQuestion.objects.create(
                    module=module,
                    question_text=q['question_text'],
                    option_a=q['option_a'],
                    option_b=q['option_b'],
                    option_c=q['option_c'],
                    option_d=q['option_d'],
                    correct_option=q['correct_option'],
                )
                questions_created += 1

        return modules_created, questions_created, practices_backfilled, scenarios_expanded

    # ---- Part 2: phishing data ----

    def _seed_templates(self):
        created_count = 0
        fixed_count = 0
        tracked_fields = ['subject_line', 'sender_name', 'sender_email', 'body_content', 'channel', 'difficulty']
        for spec in TEMPLATES:
            existing = EmailTemplate.objects.filter(name=spec['name']).first()
            if existing:
                changed_fields = [f for f in tracked_fields if getattr(existing, f) != spec[f]]
                if changed_fields:
                    for f in changed_fields:
                        setattr(existing, f, spec[f])
                    existing.save(update_fields=changed_fields)
                    fixed_count += 1
                    self.stdout.write(f"  Corrected template content: {spec['name']}")
                else:
                    self.stdout.write(f"  Skipping template (already correct): {spec['name']}")
                continue
            EmailTemplate.objects.create(
                name=spec['name'],
                subject_line=spec['subject_line'],
                sender_name=spec['sender_name'],
                sender_email=spec['sender_email'],
                body_content=spec['body_content'],
                channel=spec['channel'],
                difficulty=spec['difficulty'],
            )
            created_count += 1
            self.stdout.write(f"  Created template: {spec['name']}")
        return created_count, fixed_count

    def _seed_campaigns(self):
        created_count = 0
        fixed_count = 0
        campaigns = []
        now = timezone.now()

        admin_profile = Profile.objects.filter(role='admin').first()
        created_by = admin_profile.user if admin_profile else User.objects.filter(is_superuser=True).first()

        for spec in CAMPAIGNS:
            correct_template = EmailTemplate.objects.get(name=spec['template_name'])
            existing = PhishingCampaign.objects.filter(name=spec['name']).first()
            if existing:
                if existing.template_id != correct_template.id:
                    self.stdout.write(
                        f"  Correcting campaign template: {spec['name']} "
                        f"[was: {existing.template.name}] -> [{correct_template.name}]"
                    )
                    existing.template = correct_template
                    existing.save(update_fields=['template'])
                    fixed_count += 1
                else:
                    self.stdout.write(f"  Skipping campaign (already correct): {spec['name']}")
                campaigns.append(existing)
                continue

            campaign = PhishingCampaign.objects.create(
                name=spec['name'],
                description=f"Simulated phishing exercise: {spec['name']}.",
                template=correct_template,
                created_by=created_by,
                status='active',
                start_date=now,
                end_date=now + timedelta(weeks=2),
            )
            created_count += 1
            campaigns.append(campaign)
            self.stdout.write(f"  Created campaign: {campaign.name} (template: {correct_template.name})")

        return created_count, fixed_count, campaigns

    def _seed_results(self, campaigns):
        employees = list(User.objects.filter(profile__role='employee'))
        created_count = 0

        for employee in employees:
            # Decide how many campaigns get an "actioned" outcome for this employee,
            # guaranteeing at least one always stays unactioned so there's something
            # to demo live for every employee, regardless of how many campaigns exist.
            shuffled = campaigns[:]
            random.shuffle(shuffled)
            num_actioned = random.randint(0, max(0, len(shuffled) - 1))
            actioned = set(c.id for c in shuffled[:num_actioned])

            for campaign in campaigns:
                if PhishingResult.objects.filter(campaign=campaign, employee=employee).exists():
                    continue

                if campaign.id in actioned:
                    if random.random() < 0.5:
                        PhishingResult.objects.create(
                            campaign=campaign,
                            employee=employee,
                            clicked_link=True,
                            clicked_at=timezone.now(),
                        )
                    else:
                        PhishingResult.objects.create(
                            campaign=campaign,
                            employee=employee,
                            reported_suspicious=True,
                        )
                else:
                    PhishingResult.objects.create(campaign=campaign, employee=employee)

                created_count += 1

        return created_count

    def _ensure_demoable_unactioned_result(self, campaigns):
        """
        For employees whose results were ALL already actioned before this command
        ran (e.g. from an earlier seeding pass), reset one existing result back to
        unactioned so every employee has something to demo (Open Email / Report as
        Suspicious). Only touches employees with zero unactioned results — never
        touches an employee who already has one.
        """
        fixed_count = 0
        employees = User.objects.filter(profile__role='employee')

        for employee in employees:
            results = PhishingResult.objects.filter(employee=employee, campaign__in=campaigns)
            if not results.exists():
                continue
            if results.filter(clicked_link=False, reported_suspicious=False).exists():
                continue

            # Prefer resetting a clicked-only (not reported) result, to avoid
            # undoing a "reported" success story.
            target = results.filter(reported_suspicious=False).first() or results.first()
            target.clicked_link = False
            target.clicked_at = None
            target.reported_suspicious = False
            target.save()
            fixed_count += 1
            self.stdout.write(
                f"  Reset {employee.username}'s result on '{target.campaign.name}' to unactioned for demo purposes"
            )

        return fixed_count
